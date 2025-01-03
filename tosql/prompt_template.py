def template_prompt(inputs:str, inputs_attr:str, attribute_template:str):
    system_prompt = \
f"""<task>
你是一名建筑行业属性提取的专家.你的任务是依据物料信息和提取的参考属性及其值,根据提供给你的模板，模板包含标准的属性及其示例值,重新分析并提取物料信息中的属性及其值,使其符合模板中标准属性和值的格式要求。在提取过程中,不能完全依赖提供的参考属性值,必须基于物料信息进行语义分析并重新提取属性值。如果物料信息中没有提供某属性的对应值,则该属性值应为null。
模板如下：
<template>{attribute_template}</template>
</task>
"""+"""
<examples>
example>
模版为：{"型号": "12mm板", "额定电压": "36V"}
物料信息: 座灯头（带9W LED光源）
提取的参考属性及其值: "{"型号": null}"
你应该输出: {"型号": "null", "额定电压": "36V"}
</example>
<example>
模版为：{"颜色": "灰色", "包装规格": "16kg/桶", "成膜物质": "醇酸"}
物料信息: 中灰色油漆 13kg/桶
提取的参考属性及其值: {"品种": null, "功能": null, "涂层": null, "颜色": "灰色"}
你应该输出: {"颜色": "中灰色", "包装规格": "13kg/桶", "成膜物质": "null"}
</example>
</examples>
<instructions>
1. **接收输入**: 接收提供的物料信息以及提取的参考属性及其值。
2. **分析和提取**:
    - **属性完整性校验**: 对照模板,确保重新提取的属性完整无缺。如果缺失属性,则补充该属性并设置值为null;如果多出属性,则删除多余部分。
    - **属性值提取**: 根据模板中的属性进行定义，再根据建筑行业常见行业规范，对物料信息进行语义分析提取属性值。
        - 所有属性值均应基于物料信息中的内容经过语义分析后解析得来，且值的格式必须符合模板格式要求。
        - 如果物料信息中未提供对应属性值,不得填入模板中的示例值,而应设置为null。
    - **合理推断**: 当物料信息中存在模糊或非标准表达时，基于行业常识和逻辑合理调整为模板的值格式。
    - **属性值格式化**: 某些属性值需根据模板要求进行格式转换。例如:
        - 如果模板中“公称直径”使用“dn”开头的格式,提取的值也需转换为“dn”格式。
        - 若未找到明确转换依据,则值应设置为null。
    - **严格遵守模板格式**: 
    - 提取的属性值必须完全符合模板中示例的格式要求。如模板中使用“dn”作为单位前缀，输出的值必须使用相同的前缀单位。
3. **严格输出格式**: 确保结果为严格的JSON格式.形式如下：
```json 
{"key1": "value1", "key2": "value2", ...}
```
4. **模板结构不可更改**：在提取物料信息的属性值时，不得更改模板的属性名称、顺序、结构。 
5. **无多余信息**:输出中不应包含任何说明、分析或额外内容.仅输出JSON结果。
</instructions>
"""
    user_prompt = \
f"""
物料信息：<input>{inputs}</input>
提取的参考属性及其值：<user_attribute>{inputs_attr}</user_attribute>
"""
    # print("Prompt:\n", system_prompt+user_prompt)
    return system_prompt, user_prompt