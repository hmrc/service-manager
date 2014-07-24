# Format string may contain two special values '$s' will be replaced by 's' if the list has more than one value, $list will be replaced by the list.
def pretty_print_list(format_string, values, default_if_empty=""):

    if not values:
        return default_if_empty

    if len(values) == 1:
        s = ""
        list_string = "'%s'" % values[0]
    else:
        s = "s"
        list_string = ", ".join("'{0}'".format(w) for w in values[:-1]) + (" and '%s'" % values[-1])

    return format_string.replace("$s", s).replace("$list", list_string)


def if_not(value, default_value):
    return value if value else default_value


def unify_lists(*lists):
    result = []

    for a_list in lists:
        result += if_not(a_list, [])

    unique_results = list(set(result))

    return if_not(unique_results, None)