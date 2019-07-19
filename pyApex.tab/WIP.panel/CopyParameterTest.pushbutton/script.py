__beta__ = True
from pyrevit import revit, DB
import pyapex_parameters as pyap
element_id_int = 2442



def collect_parameters(element, prefix=""):
    result = set()
    prefix = prefix.lower()
    for p in element.Parameters:
        p_def = p.Definition

        if p_def.Name.lower().startswith(prefix):
            result.add(p_def)
    return result

test_values = [
    "Input1_Double -> Output2_Length",
    "Input5_String_Float -> Output2_Length",
    "Input2_Length -> Output4_String",
    "Input7_ElementId -> Output3_Integer"
]
test_values =[]
def main():
    print("run")
    element = revit.doc.GetElement(DB.ElementId(element_id_int))
    input_parameters = collect_parameters(element, "input")
    output_parameters = collect_parameters(element, "output")
    input_parameters = sorted(input_parameters, key=lambda d: d.Name)
    output_parameters = sorted(output_parameters, key=lambda d: d.Name)

    with revit.TransactionGroup():
        # clean parameters
        if __shiftclick__:
            with revit.Transaction():
                for op_def in output_parameters:
                    pyap.erase_parameter(element,op_def)
        # fill parameters
        else:
            for op_def in output_parameters:
                for ip_def in input_parameters:
                    title = "%s -> %s"  % (ip_def.Name, op_def.Name)
                    if test_values and title not in test_values:
                        continue
                    print(title)
                    param_get = element.get_Parameter(ip_def)
                    param_set = element.get_Parameter(op_def)
                    p_get = pyap.parameter_value_get(param_get)

                    if (param_get.StorageType == DB.StorageType.String):
                        p_get_v = param_get.AsString()
                    else:
                        p_get_v = param_get.AsValueString()

                    with revit.Transaction():
                        try:
                            result = pyap.copy_parameter(element, ip_def, op_def)
                            print("result: %s" % str(result))
                        except Exception as exc:
                            print("Exception %s" % exc)
                    if (param_set.StorageType == DB.StorageType.String):
                        p_set_v = param_set.AsString()
                    else:
                        p_set_v = param_set.AsValueString()
                    print("%s -> %s" % (p_get_v, p_set_v))
                    print("\n")

if __name__ == '__main__':
    main()