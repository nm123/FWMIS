def get_subtree_resp_ids(resp_id, responsibilities):
    result = [resp_id]
    for resp in responsibilities:
        if resp["parent_id"] == resp_id:
            result.extend(get_subtree_resp_ids(resp["id"], responsibilities))
    return result
