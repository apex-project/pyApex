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
                    for op_def in output_parameters:
                        print("%s -> %s"  % (ip_def.Name, op_def.Name))
                        param_get = element.get_Parameter(ip_def)
                        p_get = pyap.parameter_value_get(param_get)
                        with revit.Transaction():
                            pyap.copy_parameter(element, ip_def, op_def)
                        param_set = element.get_Parameter(op_def)
                        p_set = pyap.parameter_value_get(param_set)
                        print("%s -> %s" % (str(p_get), str(p_set)))
                        print("\n")

if __name__ == '__main__':
    main()