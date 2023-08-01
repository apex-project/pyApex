import inspect
from pyrevit import script, revit, DB, HOST_APP

logger = script.get_logger()

# define globals

STORAGE_TYPES_NUMERICAL = None
FORGE_TYPES_NOT_CONVERTIBLE = None
UNIT_TYPES_NON_CONVERTIBLE = None
PARAM_ATTR_MAP = None
SKIP_ATTRS = []

def get_storage_types_numerical():
    global STORAGE_TYPES_NUMERICAL
    if not STORAGE_TYPES_NUMERICAL:
        STORAGE_TYPES_NUMERICAL = [
            DB.StorageType.Double,
            DB.StorageType.Integer,
            DB.StorageType.ElementId
        ]
    return STORAGE_TYPES_NUMERICAL


def get_unit_types_non_convertible():
    global UNIT_TYPES_NON_CONVERTIBLE
    if UNIT_TYPES_NON_CONVERTIBLE is None:
        UNIT_TYPES_NON_CONVERTIBLE = [
                None,
                DB.UnitType.UT_Number,
                DB.UnitType.UT_Undefined
            ]
    return UNIT_TYPES_NON_CONVERTIBLE
    
    
def get_forge_types_non_convertible():
    global FORGE_TYPES_NOT_CONVERTIBLE
    if FORGE_TYPES_NOT_CONVERTIBLE is None:
        FORGE_TYPES_NOT_CONVERTIBLE = [
            DB.ForgeTypeId("autodesk.spec.aec:number-1.0.0"),
            DB.ForgeTypeId("autodesk.spec:spec.string-1.0.0")
            ]
        logger.debug("FORGE_TYPES_NOT_CONVERTIBLE:")
        logger.debug(FORGE_TYPES_NOT_CONVERTIBLE)
    return FORGE_TYPES_NOT_CONVERTIBLE


def get_param_attr_map():
    global PARAM_ATTR_MAP
    if PARAM_ATTR_MAP is None:
        PARAM_ATTR_MAP = {
            int(DB.BuiltInParameter.SHEET_NUMBER): "SheetNumber"
        }
    return PARAM_ATTR_MAP


# defs


def is_empty(param):
    return param.AsString() != '' and param.AsString() != None


def are_equal(param1, param2):
    value1, value2 = convert_value(param1, param2, return_both=True)
    logger.debug("value1: %s" % str(value1))
    logger.debug("value2: %s" % str(value2))
    return value1 == value2


def are_equal_return_values(param1, param2):
    value1, value2 = convert_value(param1, param2, return_both=True)
    return value1 == value2, value1, value2


def parameter_value_string_get(parameter, conversion=True):
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
        logger.debug("param1.StorageType != param2.StorageType")
        logger.debug("%s != %s" % (str(param1.StorageType), str(param2.StorageType)))
        return False
    if unit_type and get_def_forgetypeid(param1.Definition) != get_def_forgetypeid(param2.Definition):
        logger.debug("param1.Definition.GetDataType() != param2.Definition.GetDataType()")
        logger.debug("%s != %s" % (str(get_def_forgetypeid(param1.Definition)),
                                   str(get_def_forgetypeid(param2.Definition))))
        return False
    return True


def are_param_types_almost_equal(param1, param2):
    storage_type1 = param1.StorageType
    storage_type2 = param2.StorageType
    if storage_type1 in get_storage_types_numerical():
        storage_type1 = DB.StorageType.Integer
    if storage_type2 in get_storage_types_numerical():
        storage_type2 = DB.StorageType.Integer
    return storage_type1 == storage_type2


def parameter_value_set(parameter_set, parameter_get, value_get=None, value_set_before=None):
    logger.debug("PARAMETER_VALUE_SET")
    logger.debug("parameter_set:%s, parameter_get:%s, value_get:%s, value_set_before:%s" % (
        str(parameter_set), str(parameter_get), str(value_get), str(value_set_before)))
    # if not value_set_before:
    #     value_set_before = parameter_value_get(parameter_set)
    if not value_get:
        value_get, _empty = convert_value(parameter_get, parameter_set)
    logger.debug("value_get: %s" % str(value_get))
    logger.debug("type(value_get): %s" % str(type(value_get)))
    if not value_get:
        raise Exception("Value is empty")

    # verify
    logger.debug("parameter_set.StorageType: %s" % str(parameter_set.StorageType))
    if parameter_set.StorageType == DB.StorageType.ElementId:
        verify_element_id(parameter_set, value_get)
        # todo optimise verification of other types, to check before applying parameter

    if parameter_set.StorageType in [DB.StorageType.Double, DB.StorageType.Integer]:
        if isinstance(value_get, DB.ElementId):
            value_get = value_get.IntegerValue
        logger.debug("DB.StorageType.Double, DB.StorageType.Integer")
        if isinstance(value_get, float) or isinstance(value_get, int):
            logger.debug("parameter_set.Set(value_get)")
            parameter_set.Set(value_get)
        else:
            logger.debug("parameter_set.SetValueString(str(value_get))")
            parameter_set.SetValueString(str(value_get))

    elif parameter_set.StorageType == DB.StorageType.String:
        logger.debug("DB.StorageType.String")
        logger.debug("parameter_set.Set(str(value_get))")
        parameter_set.Set(str(value_get))

    elif parameter_set.StorageType == DB.StorageType.ElementId:
        logger.debug("DB.StorageType.ElementId")
        if isinstance(value_get, DB.ElementId):
            logger.debug("parameter_set.Set(value_get)")
            parameter_set.Set(value_get)
        elif isinstance(value_get, int) or isinstance(value_get, float):
            logger.debug("parameter.Set(DB.ElementId(value))")
            parameter_set.Set(DB.ElementId(value_get))
        else:
            raise Exception("Incorrect value type for ElementId")
    else:
        raise Exception("Unexpected Storate Type")
    # if are_param_types_equal(parameter_get, parameter_set):
    #     parameter_set.Set(value_get)
    #     logger.debug("parameter.Set(value)")
    #     logger.debug(value_get)
    # elif isinstance(value_get, int) and parameter_set.StorageType == DB.StorageType.ElementId:
    #     parameter_set.Set(DB.ElementId(value_get))
    #     logger.debug("parameter.Set(DB.ElementId(value))")
    #     logger.debug(value_get)
    # elif parameter_set.StorageType == DB.StorageType.String:
    #     parameter_set.Set(str(value_get))
    #     logger.debug("parameter.Set(str(value))")
    #     logger.debug(value_get)
    # # set(numerical) without conversion
    # elif (isinstance(value_get, int) or isinstance(value_get, float)) and \
    #         parameter_set.StorageType in [DB.StorageType.Double, DB.StorageType.Integer] and \
    #         parameter_set.Definition.UnitType in UNIT_TYPES_NOT_CONVERTIBLE:
    #     parameter_set.Set(value_get)
    #     logger.debug("parameter.Set(value) UNIT_TYPES_NOT_CONVERTIBLE")
    #     logger.debug(value_get)
    # if types aren't equal
    # else:
    #     logger.debug("parameter.SetValueString(value)")
    #     parameter_set.SetValueString(str(value_get))

    # TODO fix check. For some reason parameter isnt being changed
    # value_set_after = parameter_value_get(parameter_set)
    # if (value_set_before == value_set_after):
    #     logger.debug("value_set_before: %s" % str(value_set_before))
    #     logger.debug("value_set_after: %s" % str(value_set_after))
    #     raise Exception("Cannot convert the value.")
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


def parameter_value_get(parameter, conversion=True):
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


def convert_value(parameter_get, parameter_set, return_both=False):
    logger.debug("CONVERT_VALUE")
    value_set = None
    # try to get numerical value

    # If parameters are equal, get original value
    if are_param_types_equal(parameter_get, parameter_set):
        logger.debug("param types are equal")
        value = parameter_value_get(parameter_get, conversion=False)
        if return_both:
            value_set = parameter_value_get(parameter_set, conversion=False)

    # e.g. Length -> String, ElementId -> String
    elif parameter_get.StorageType in get_storage_types_numerical() \
            and parameter_set.StorageType == DB.StorageType.String:
        logger.debug("param types are not equal (get Numerical -> set String)")
        # e.g. Double -> String, ElementId -> String
        if is_parameter_convertible(parameter_get):
            logger.debug("parameter_get is convertible: %s" % get_def_forgetypeid(parameter_get.Definition))
            if parameter_get.StorageType == DB.StorageType.ElementId:
                value = parameter_get.AsString()
            else:
                value = parameter_get.AsValueString()
            if return_both:
                value_set = parameter_get.AsString()
        else:
            logger.debug("parameter_get is not convertible: %s" % get_def_forgetypeid(parameter_get.Definition))
            value = parameter_value_string_get(parameter_get, conversion=False)
            if return_both:
                value_set = parameter_value_string_get(parameter_set, conversion=False)
            # e.g. Length -> String
    else:
        logger.debug("param types are not equal (any -> any)")
        # if not, first try to get PRE VALUE
        if parameter_get.StorageType in get_storage_types_numerical():
            logger.debug("parameter_get.StorageType in STORAGE_TYPES_NUMERICAL")
            value_get_pre = parameter_value_get(parameter_get, conversion=False)
        else:
            value_get_pre = parameter_value_string_get(parameter_get)

        if isinstance(value_get_pre, int) or isinstance(value_get_pre, float) and \
                parameter_set.StorageType in get_storage_types_numerical():
            logger.debug("value_get is int or float; param_set is also numerical")
            value = value_get_pre
            if return_both:
                value_set = parameter_value_get(parameter_set, conversion=False)

            # if target is convertable.. (e.g. convert Number to Length)
            if not is_parameter_convertible(parameter_get) and is_parameter_convertible(parameter_set):
                logger.debug("value get is non-convertible, but set is convertible")
                logger.debug("value: %s" % str(value))
                # FIXME workaround for Revit older than 2021 when UnitType was deprecated
                if HOST_APP.is_newer_than(2020):
                    logger.debug("DB.UnitUtils.ConvertToInternalUnits to %s" % str(parameter_set.GetUnitTypeId()))
                    value = DB.UnitUtils.ConvertToInternalUnits(value, parameter_set.GetUnitTypeId())
                else:
                    logger.debug("DB.UnitUtils.ConvertToInternalUnits to %s" % str(parameter_set.DisplayUnitType))
                    value = DB.UnitUtils.ConvertToInternalUnits(value, parameter_set.DisplayUnitType)

                logger.debug("value converted: %s" % str(value))

            # if source is convertable.. (e.g. convert Length to Number)
            elif is_parameter_convertible(parameter_get) and not is_parameter_convertible(parameter_set):
                logger.debug("value get is convertible, but set is non-convertible")
                logger.debug("value: %s" % str(value))
                # FIXME workaround for Revit older than 2021 when UnitType was deprecated
                if HOST_APP.is_newer_than(2020):
                    logger.debug("DB.UnitUtils.ConvertFromInternalUnits to %s" % str(parameter_set.GetUnitTypeId()))
                    value = DB.UnitUtils.ConvertFromInternalUnits(value, parameter_get.GetUnitTypeId())
                else:
                    logger.debug("DB.UnitUtils.ConvertFromInternalUnits to %s" % str(parameter_set.DisplayUnitType))
                    value = DB.UnitUtils.ConvertFromInternalUnits(value, parameter_get.DisplayUnitType)

                logger.debug("value converted: %s" % str(value))

        elif isinstance(value_get_pre, str) and parameter_set.StorageType not in get_storage_types_numerical():
            logger.debug("value_get is str or float; param_set is numerical")
            value = value_get_pre
            if return_both:
                value_set = parameter_value_string_get(parameter_set)
        # Input is String (Text, not a number) and target is a number
        else:
            logger.debug("other case - no conversion needed")
            # raise Exception("Cannot parse string to numerical value")
            # Try to set it anyway, for ElementId should work
            value = value_get_pre
            if return_both:
                value_set = parameter_value_get(parameter_set)

    return value, value_set


def copy_parameter(element, definition_get, definition_set):
    param_set = element.get_Parameter(definition_set)
    param_get = element.get_Parameter(definition_get)
    # check if values are equal
    are_equal_bool, value_get, value_set_before = are_equal_return_values(param_get, param_set)
    logger.debug("are_equal_bool: %s" % str(are_equal_bool))
    if are_equal_bool:
        return False
    return parameter_value_set(param_set, param_get, value_get=value_get)  #, value_set_before=value_set_before


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


def get_selection_parameters(elements,
                             ignore_types=(),
                             attributes=True,
                             attr_allow_types=(str, int, float),
                             check_on_all_elements=True,
                             mlogger=None):
    """
    Get parameters which are common for all selected elements

    :param elements: list of elements
    :param ignore_types: list of StorageTypes to ignore
    :param attributes: if True, also API-attributes of elements will be shown
    :param attr_allow_types: list of types which are allowed for attributes (e.g. str, int, float)
    :param check_on_all_elements: if True, the parameter will be shown only if it is present on all elements
    :param mlogger: logger

    :return: dict of parameters
    """
    result = {}
    all_parameter_ids_by_element = {}
    definition_parameter_dict = {}
    all_attributes_by_type = {}  # list of processed classes
    # find all ids
    for e in elements:
        for p in e.Parameters:
            if p.StorageType in ignore_types:
                continue
            p_id = p.Definition.Id
            definition_parameter_dict[p_id] = p
            if e.Id not in all_parameter_ids_by_element.keys():
                all_parameter_ids_by_element[e.Id] = set()
            all_parameter_ids_by_element[e.Id].add(p_id)

        if attributes and type(e) not in all_attributes_by_type.keys():
            for attr_name in dir(e):
                if inspect.ismethod(attr_name):
                    continue
                if attr_name.startswith(
                        "__") or attr_name in SKIP_ATTRS:
                    continue
                is_readable=False
                try:
                    attr_value = getattr(e, attr_name)
                    if isinstance(attr_value, attr_allow_types) and \
                            (bool in attr_allow_types
                             or not isinstance(attr_value, bool)):

                        is_readable=True
                except Exception as exc:
                    if mlogger:
                        mlogger.debug(exc)
                    continue
                if is_readable:
                    p_id = "[%s]" % attr_name
                    definition_parameter_dict[p_id] = attr_name
                    if type(e) not in all_attributes_by_type.keys():
                        all_attributes_by_type[type(e)] = set()
                    all_attributes_by_type[type(e)].add(p_id)

    # filter
    for p_id, param in definition_parameter_dict.items():
        exists_for_all_elements = True
        if check_on_all_elements:
            if isinstance(param, str):
                for el_type, type_params in all_attributes_by_type.items():
                    if p_id not in type_params:
                        exists_for_all_elements = False
                        break
            else:
                for e_id, e_params in all_parameter_ids_by_element.items():
                    if p_id not in e_params:
                        exists_for_all_elements = False
                        break

        if exists_for_all_elements:
            if isinstance(param, str):
                result[p_id] = param
            else:
                p_def = param.Definition
                # skip duplicates by name, if existing one is modifiable
                if p_def.Name in result.keys():
                    if mlogger:
                        mlogger.debug(
                            "exists %s %d" % (p_def.Name, p_def.Id.IntegerValue))
                    if not result[p_def.Name].IsReadOnly:
                        if mlogger:
                            mlogger.debug(
                                "skip %s %d" % (p_def.Name, p_def.Id.IntegerValue))
                        continue
                # add to results
                if mlogger:
                    mlogger.debug("add %s %d" % (p_def.Name, p_def.Id.IntegerValue))
                result[p_def.Name] = param

    return result


def filter_editable(elements,
                    parameters,
                    override_attrs=True,
                    ignore_types=(DB.StorageType.ElementId,),
                    mlogger=None):
    """
    Filter parameters which can be modified by users

    :param elements: list of elements
    :param parameters: list of parameters
    :param override_attrs: if True, attribies with identical names will be shown separately (TODO check)
    :param ignore_types: list of StorageTypes to ignore
    :param mlogger: logger

    :return: filtered list of parameters
    """

    # get exceptions
    dry_transaction = None
    editable_attrs = []
    for name, param in parameters.items():
        if isinstance(param, str):
            if not dry_transaction:
                dry_transaction = DB.Transaction(revit.doc, "dry_transaction")
                dry_transaction.Start()
            for element in elements:
                try:
                    setattr(element, param, "0")
                    editable_attrs.append(param)
                    break
                except Exception as exc:
                    if mlogger:
                        mlogger.debug("filter_editable attr exc %s" % exc)

        elif override_attrs:
            param_id = param.Definition.Id.IntegerValue
            if param_id in get_param_attr_map().keys():
                param_name = get_param_attr_map()[param_id]
                editable_attrs.append(param_name)
                parameters[name] = param_name
    if dry_transaction:
        if not dry_transaction.HasEnded():
            dry_transaction.RollBack()

    result = {n: p for n, p in parameters.iteritems()
              if (isinstance(p, str)
                  and p in editable_attrs)
              or (not isinstance(p,str)
                  and not p.IsReadOnly and p.StorageType not in ignore_types)}
    return result


def definition_or_name(param):
    """
    Get parameter definition or name
    """
    if isinstance(param, str):
        return param
    else:
        return param.Definition


def get_def_forgetypeid(definition):
    """
    Workaround to get the script working in Revit <2021 and <2022
    (UnitType is deprecated since 2021 though still available,
    GetSpecTypeId() added in 2021 and deprecated in 2022,
    GetDataType() available since 2022)
    """
    if HOST_APP.is_newer_than(2021):
        return definition.GetDataType()
    else:
        return definition.UnitType


def is_forgetypeid_convertible(forge_type_id):
    """
    Check if ForgeTypeId is convertible (not mentioned in list)
    """
    if "ForgeTypeId" in dir(DB) and isinstance(forge_type_id, DB.ForgeTypeId):
        if not forge_type_id:
            return False
        for _fti in get_forge_types_non_convertible():
            if _fti.NameEquals(forge_type_id):
                return False
        return True
    else:
        return forge_type_id not in get_unit_types_non_convertible()


def is_parameter_convertible(param):
    return is_forgetypeid_convertible(get_def_forgetypeid(param.Definition))
