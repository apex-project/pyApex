from pyrevit import script, DB

logger = script.get_logger()

STORAGE_TYPES_NUMERICAL = [
    DB.StorageType.Double,
    DB.StorageType.Integer,
    DB.StorageType.ElementId
]
UNIT_TYPES_NOT_CONVERTIBLE = [
    None,
    DB.UnitType.UT_Number,
    DB.UnitType.UT_Undefined
]


def is_empty(param):
    return param.AsString() != '' and param.AsString() != None

def are_equal(param1, param2):
    value1 = convert_value(param1, param2)
    value2 = convert_value(param2, param1)
    return value1 == value2

def are_equal_return_value(param1, param2):
    value1 = convert_value(param1, param2)
    result = are_equal_value_param(value1, param1, param2)
    return result, value1

def are_equal_value_param(value1, param1, param2):
    value2 = convert_value(param2, param1)
    return value1 == value2

def parameter_value_string_get(parameter, conversion = True):
    logger.debug("parameter_value_string_get")
    x = None
    if conversion:
        x = int_or_float_try_parse_parameter(parameter)
    if not x:
        logger.debug("parameter.StorageType: %s" % str(parameter.StorageType))
        if parameter.StorageType == DB.StorageType.String:
            x = parameter.AsString()
            logger.debug("parameter_value_string_get AsString")
        else:
            x = parameter.AsValueString()
            logger.debug("parameter_value_string_get AsValueString")
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
    if parameter.StorageType == DB.StorageType.String:
        return float_try_parse(parameter.AsString())
    else:
        return float_try_parse(parameter.AsValueString())


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



def are_param_types_equal(param1, param2, storage_type=True, unit_type=True):
    if storage_type and param1.StorageType != param2.StorageType:
        logger.debug("param1.StorageType, param2.StorageType")
        logger.debug("%s, %s" % (str(param1.StorageType), str(param2.StorageType)))
        return False
    if unit_type and param1.Definition.UnitType != param2.Definition.UnitType:
        logger.debug("param1.Definition.UnitType, param2.Definition.UnitType")
        logger.debug("%s, %s" % (str(param1.Definition.UnitType), str(param2.Definition.UnitType)))
        return False
    return True


def are_param_types_almost_equal(param1, param2):
    storage_type1 = param1.StorageType
    storage_type2 = param2.StorageType
    if storage_type1 in STORAGE_TYPES_NUMERICAL:
        storage_type1 = DB.StorageType.Integer
    if storage_type2 in STORAGE_TYPES_NUMERICAL:
        storage_type2 = DB.StorageType.Integer
    return storage_type1 == storage_type2


def parameter_value_set(parameter_set, parameter_get, value = None):
    logger.debug("PARAMETER_VALUE_SET")
    value_before = parameter_value_get(parameter_set)
    if not value:
        value = convert_value(parameter_get, parameter_set)

    if not value:
        raise Exception("Value is empty")

    # verify
    logger.debug("parameter_set.StorageType: %s" % str(parameter_set.StorageType))
    if parameter_set.StorageType == DB.StorageType.ElementId:
        verify_element_id(parameter_set, value)
        # todo optimise verification of other types, to check before applying parameter

    if are_param_types_equal(parameter_get, parameter_set):
        parameter_set.Set(value)
        logger.debug("parameter.Set(value)")
        logger.debug(value)
    elif isinstance(value, int) and parameter_set.StorageType == DB.StorageType.ElementId:
        parameter_set.Set(DB.ElementId(value))
        logger.debug("parameter.Set(DB.ElementId(value))")
        logger.debug(value)
    elif parameter_set.StorageType == DB.StorageType.String:
        parameter_set.Set(str(value))
        logger.debug("parameter.Set(str(value))")
        logger.debug(value)
    # set(numerical) without conversion
    elif (isinstance(value, int) or isinstance(value, float)) and \
            parameter_set.StorageType in [DB.StorageType.Double, DB.StorageType.Integer] and \
            parameter_set.Definition.UnitType in UNIT_TYPES_NOT_CONVERTIBLE:
        parameter_set.Set(value)
        logger.debug("parameter.Set(value) UNIT_TYPES_NOT_CONVERTIBLE")
        logger.debug(value)
    # if types aren't equal
    else:
        logger.debug("parameter.SetValueString(value)")
        parameter_set.SetValueString(str(value))
    value_after = parameter_value_get(parameter_set)
    if(value_before == value_after):
        raise Exception("Cannot convert the value.")
    return True


def verify_element_id(parameter_set, value):
    logger.debug("verify_element_id")
    if parameter_set.StorageType != DB.StorageType.ElementId:
        raise Exception("verify_element_id: parameter_set.StorageType is not ElementId")
    doc = parameter_set.Element.Document
    try:
        element_id = value if isinstance(value, DB.ElementId) else DB.ElementId(int(value))
    except:
        raise Exception("verify_element_id: unable to create element id")
    element = doc.GetElement(element_id)
    if not element:
        raise Exception("verify_element_id: element not found")
    logger.debug("element: %s" % str(element))
    if not isinstance(element, DB.FamilyType):
        raise Exception("verify_element_id: element is not a family type")
    # todo check if the element is of a certain type


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
        logger.debug("parameter_value_get ElementId AsElementId")
        x = parameter.AsElementId()
        if conversion:
            logger.debug("conversion_elementid==True, get ElementId.IntegerValue")
            x = x.IntegerValue
    else:
        x = parameter_value_string_get(parameter, conversion)
    return x


def convert_value(parameter_get, parameter_set):
    if not are_param_types_equal(parameter_get, parameter_set):

        # first check if storage type are equal and Double
        logger.debug("parameter_get.StorageType: %s " % str(parameter_get.StorageType))
        logger.debug("parameter_set.StorageType: %s " % str(parameter_set.StorageType))
        logger.debug("parameter_get.Definition.UnitType: %s" % str(parameter_get.Definition.UnitType))
        logger.debug("parameter_set.Definition.UnitType: %s" % str(parameter_set.Definition.UnitType))
        if are_param_types_almost_equal(parameter_get, parameter_set) \
                and parameter_get.StorageType in STORAGE_TYPES_NUMERICAL:
            logger.debug("are_param_types_almost_equal(parameter_get ...")
            value = parameter_value_get(parameter_get, conversion=False)
            # if GET is raw and SET is not raw (should be converted)
            if parameter_get.Definition.UnitType in UNIT_TYPES_NOT_CONVERTIBLE \
                and parameter_set.Definition.UnitType not in UNIT_TYPES_NOT_CONVERTIBLE:
                logger.debug("DB.UnitUtils.ConvertToInternalUnits to %s" % str(parameter_set.DisplayUnitType))
                value = DB.UnitUtils.ConvertToInternalUnits(value,
                                                            parameter_set.DisplayUnitType)
        else:
            logger.debug("not are_param_types_almost_equal(parameter_get ...")
            value = parameter_value_string_get(parameter_get)
    else:
        value = parameter_value_get(parameter_get, conversion=False)
    return value


def copy_parameter(element, definition_get, definition_set):
    param_set = element.get_Parameter(definition_set)
    param_get = element.get_Parameter(definition_get)
    # check if values are equal
    are_equal_bool, value1 = are_equal_return_value(param_get, param_set)
    if are_equal_bool:
        return False
    return parameter_value_set(param_set, param_get, value1)

def erase_parameter(element, definition):
    param = element.get_Parameter(definition)
    if param.StorageType == DB.StorageType.Double:
        param.Set.Overloads[float](0)
    elif param.StorageType == DB.StorageType.Integer:
        param.Set.Overloads[int](0)
    elif param.StorageType == DB.StorageType.ElementId:
        param.Set.Overloads[DB.ElementId](DB.ElementId.InvalidElementId)
    else:
        param.Set.Overloads[str](None)
