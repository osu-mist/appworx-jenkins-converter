import re


def exp_to_json(file_path):

    def _reset_switches():
        global is_job_table, is_documentation, is_module_sched, is_chain_detail
        global is_job_prompts, is_object_cond

        is_job_table = False
        is_documentation = False
        is_chain_detail = False
        is_module_sched = False
        is_job_prompts = False
        is_object_cond = False

    # global switches
    global is_job_table, is_documentation, is_module_sched, is_chain_detail
    global is_job_prompts, is_object_cond

    # section index
    module_sched_idx = chain_idx = -1

    exp_json = {
        'aw_module_sched': [],
        'so_chain_detail': [],
        'so_job_table': {},
        'so_job_prompts': [],
        'so_object_cond': {}
    }

    check_dict = {
        'B': [],  # program types
        'D': [],  # data type
        'G': [],  # agent groups
        'K': [],  # applications
        'L': [],  # libraries
        'M': [],  # modules/jobs
        'n': [],  # notifications environment
        'O': [],  # logins
        'P': [],  # output devices
        'Q': [],  # queues
        'R': [],  # user groups
        'T': [],  # output groups
        'U': []   # users
    }

    _reset_switches()

    with open(file_path, 'r') as f:

        for line in f:
            # if line is too long, combine the next line
            if line.endswith('\\\n'):
                line = line.rstrip('\\\n') + re.search(r'^.*?=(.*)', next(f)).group(1)

            # ************************************************
            # parse check options
            # ************************************************

            if line.startswith('CHECK'):
                match = re.search(r'^CHECK (.*) (.*)', line)
                check_dict[match.group(1)].append(match.group(2))

            # ************************************************
            # control swtiches and intialize job/chain section
            # ************************************************

            # so_job_table
            if line.startswith('START=so_job_table'):
                is_job_table = True
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)
                exp_json['so_job_table'] = {
                    'so_module': so_module,
                    'params': {'roles': []}
                }
                continue

            # so_documentation
            if line.startswith('START=so_documentation'):
                is_documentation = True
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)
                so_doc_source = re.search(r'so_doc_source=([^\s]*)', line).group(1)
                so_doc_type = re.search(r'so_doc_type=([^\s]*)', line).group(1)
                exp_json['so_documentation'] = {
                    'so_module': so_module,
                    'so_doc_source': so_doc_source,
                    'so_doc_type': so_doc_type,
                    'so_doc_text': ''
                }
                continue

            # aw_module_sched
            if line.startswith('START=aw_module_sched'):
                is_module_sched = True
                module_sched_idx += 1
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)
                aw_sch_name = re.search(r'aw_sch_name=([^\s]*)', line).group(1)
                exp_json['aw_module_sched'].append({
                    'so_module': so_module,
                    'aw_sch_name': aw_sch_name,
                    'params': {}
                })
                continue

            # so_chain_detail
            if line.startswith('START=so_chain_detail'):
                is_chain_detail = True
                chain_idx += 1
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)
                so_task_name = re.search(r'so_task_name=([^\s]*)', line).group(1)
                exp_json['so_chain_detail'].append({
                    'so_module': so_module,
                    'so_task_name': so_task_name,
                    'params': {}
                })
                continue

            # so_job_prompts
            if line.startswith('START=so_job_prompts'):
                is_job_prompts = True
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)
                so_prompt = re.search(r'so_prompt=([^\s]*)', line).group(1)
                exp_json['so_job_prompts'].append({
                    'so_module': so_module,
                    'so_prompt': so_prompt,
                    'params': {}
                })
                continue

            # so_object_cond
            if line.startswith('START=so_object_cond'):
                is_object_cond = True
                so_module = re.search(r'so_module=([^\s]*)', line).group(1)

                task_pattern = r'so_task_name=([^\s]*)'
                so_task_name = None if not re.search(task_pattern, line) else re.search(task_pattern, line).group(1)
                so_soc_order = re.search(r'so_soc_order=([^\s]*)', line).group(1)
                so_obj_type = re.search(r'so_obj_type=([^\s]*)', line).group(1)

                if so_task_name not in exp_json['so_object_cond']:
                    exp_json['so_object_cond'][so_task_name] = {
                        'so_module': so_module,
                        'so_obj_type': so_obj_type,
                        'conditions': []
                    }

                exp_json['so_object_cond'][so_task_name]['conditions'].append({
                    'so_soc_order': so_soc_order
                })

                continue

            # reset all switches if END
            if line.startswith('END'):
                _reset_switches()

            # **********************************************
            # add matched results to correspoinding sections
            # **********************************************

            match = re.search(r'^(.*?)=(.*)', line)

            # job_table
            if match and is_job_table:
                if match.group(1) == 'roles':
                    exp_json['so_job_table']['params'][match.group(1)] += match.group(2).split()
                else:
                    exp_json['so_job_table']['params'][match.group(1)] = match.group(2)

            # documentation
            elif match and is_documentation:
                exp_json['so_documentation']['so_doc_text'] += match.group(2)

            # module_sched
            elif match and is_module_sched:
                exp_json['aw_module_sched'][module_sched_idx]['params'][match.group(1)] = match.group(2)

            # chain_detail
            elif match and is_chain_detail:
                chain_params = exp_json['so_chain_detail'][chain_idx]['params']
                if match.group(1) == 'so_predecessors':
                    chain_params[match.group(1)] = re.findall(r'&/(.*?) =', match.group(2))
                else:
                    chain_params[match.group(1)] = match.group(2)

            # job_prompts
            elif match and is_job_prompts:
                exp_json['so_job_prompts'][int(so_prompt)-1]['params'][match.group(1)] = match.group(2)

            # object_cond
            elif match and is_object_cond:
                exp_json['so_object_cond'][so_task_name]['conditions'][int(so_soc_order)-1][match.group(1)] = match.group(2)

            # TODO: need to handle line starts with 'DELETE'?

    exp_json['checks'] = check_dict
    return exp_json
