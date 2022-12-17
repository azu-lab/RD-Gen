## How to write config file

![image](https://user-images.githubusercontent.com/55824710/205211293-b8d1232f-ca91-4b91-9f4d-52a009ccb703.png)
![image](https://user-images.githubusercontent.com/55824710/205211338-284b2550-ca2d-488b-a0f1-b34bcb2fd77d.png)

For parameters that require a numeric input, users can specify values in the following three ways:
1. **Fixed**: Only one value is specified, and this value is always used when a DAG is generated. This specification method can be used for DAGs in which end-to-end
deadlines are considered, and one exit node is always desired.
2. **Random**: When a DAG is generated, one value is randomly selected using uniform distribution from an input range. This is the most basic specification method that is used when there is no special intended value and when it is desirable to have a variety of values.
3. **Combination**: RD-Gen generates DAGs for all combinations of all lists of parameters for which Combination is specified. This specification method allows all DAG sets used in random evaluations in DAG studies to be generated in single command execution. Therefore, RD-Gen can significantly reduce the time and effort required by researchers to generate DAGs. For example, when Combination of Number of nodes is [10, 20] and Combination of Number of entry nodes is [1, 3], RDGen generates 100 DAGs for all combinations.

When specifying ranges for Random and Combination in RD-Gen, the following two intuitive descriptions are possible.
1. **List format**: The user specifies their choices in a list (array) format (such as [10, 20]).
2. **Tuple format**: The user specifies a start value, a stop value, and a step (such as (start=1, stop=3, step=1)). The tuple format is internally expanded into a list format of values that are sequentially added from the start value to the stop value at an interval of size step (e.g., (start=1, stop=3, step=1) expands to a list of [1, 2, 3]). Here, “start=,” “stop=,” and “step=” are optional.
