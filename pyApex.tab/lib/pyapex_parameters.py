from pyrevit import script, DB

logger = script.get_logger()

def is_empty(param):
    return param.AsString() != '' and param.AsString() != None

def are_equal(param1, param2):
    value1 = convert_value(param1, param2)
    value2 = convert_value(param2, param1)
    return value1 == value2

def parameter_value_string_get(parameter, conversion = True):
    logger.debug("parameter_value_string_get")
    x = None
    if conversion:
        x = int_or_float_try_parse_parameter(parameter)
    if not x:
        x = parameter.AsString()
        logger.debug("parameter_value_string_get AsString")
        logger.debug(x)
    return x


def int_or_float_try_parse_parameter(parameter):
    x = float_try_parse_parameter(parameter)
    if not x:
        return
    else:
        if x == int(x):
            return int(x)
        else:
            return x


def float_try_parse_parameter(parameter):
    x = None
    try:
        x = float_try_parse(parameter.AsValueString())
    except:
        pass
    if not x:
        x = float_try_parse(parameter.AsString())
    return x


def float_try_parse(text):
    if not text:
        return
    text = text.strip()
    if len(text) == 0:
        return
    x = None
    try:
        x = float(text)
    except:
        pass
    try:
        x = float(text.replace(".", ","))
    except:
        pass
    try:
        x = float(text.replace(",", "."))
    except:
        pass
    return x


def parameter_value_set(parameter_set, parameter_get):
    logger.debug("PARAMETER_VALUE_SET")
    value = convert_value(parameter_get, parameter_set)
    logger.debug(value)
    if not value:
        return False
    if parameter_get.StorageType != parameter_set.StorageType:
        parameter_set.SetValueString(str(value))
        logger.debug("parameter.SetValueString(value)")
    elif parameter_set.StorageType == parameter_get.StorageType:
        parameter_set.Set(value)
        logger.debug("parameter.Set(value)")
    elif parameter_set.StorageType == DB.StorageType.String:
        parameter_set.Set(str(value))
        logger.debug("parameter.Set(str(value))")
    else:
        logger.debug("parameter.SetValueString(value)")
        parameter_set.SetValueString(value)
    return True

def parameter_value_get(parameter, conversion = True):
    logger.debug("PARAMETER_VALUE_GET")
    logger.debug(parameter.Definition.Name)
    if not parameter.HasValue:
        return

    if parameter.StorageType == DB.StorageType.Double:
        logger.debug("parameter_value_get AsDouble")
        x = parameter.AsDouble()
    elif parameter.StorageType == DB.StorageType.Integer:
        logger.debug("parameter_value_get AsInteger")
        x = int(parameter.AsInteger())
    elif parameter.StorageType == DB.StorageType.ElementId:
        logger.debug("parameter_value_get ElementId AsInteger")
        x = int(parameter.AsInteger())
    else:
        return parameter_value_string_get(parameter, conversion)
    return x


def convert_value(parameter_get, parameter_set):
    if parameter_get.StorageType != parameter_set.StorageType:
        value = parameter_value_string_get(parameter_get)
    else:
        value = parameter_value_get(parameter_get, conversion=False)
    return value


def copy_parameter(element, definition_get, definition_set):
    param_set = element.get_Parameter(definition_set)
    param_get = element.get_Parameter(definition_get)
    if param_set.StorageType == param_get.StorageType:
        if are_equal(param_set, param_get):
            return False
    return parameter_value_set(param_set, param_get)

def erase_parameter(element, definition):
    param = element.get_Parameter(definition)
    param.Set(None)
