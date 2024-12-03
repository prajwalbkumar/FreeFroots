# -*- coding: utf-8 -*-
'''ParamPeel'''
__title__ = "ParamPeel"
__author__ = "prajwalbkumar"

import os
import json
from os.path import expanduser
from pyrevit import script, forms
from Autodesk.Revit.DB import *
from System.Collections.Generic import List
from System import Enum

doc = __revit__.ActiveUIDocument.Document # Get the Active Document
app = __revit__.Application # Returns the Revit Application Object

# Function to extract categories and store them in a dictionary
def extract_categories(doc):
    categories_dict = {}

    for category in doc.Settings.Categories:
        if category.BuiltInCategory != BuiltInCategory.INVALID:
            category_data = {
                "Name": category.Name,
                "BuiltInCategory": category.BuiltInCategory,
                "CategoryType": category.CategoryType.ToString()
            }
            categories_dict[category.Name] = category_data

    return categories_dict

# MAIN
categories_data = extract_categories(doc)

# Accessing Model Categories from the dictionary
model_category_names = [model_category_name for model_category_name in categories_data if categories_data[model_category_name]["CategoryType"] == "Model"]
selected_category = forms.SelectFromList.show(sorted(model_category_names), title = "Select Categories", width = 500, height = 800, multiselect = False)
if not selected_category:
    forms.alert("No Category Selected", title = "Script Exiting", warn_icon = True)
    script.exit()

selected_builtin_categories = List[BuiltInCategory]()
selected_builtin_categories.Add(categories_data[selected_category]["BuiltInCategory"])
target_elements = FilteredElementCollector(doc).WherePasses(ElementMulticategoryFilter(selected_builtin_categories)).WhereElementIsNotElementType().ToElements()

for element in target_elements:
    all_parameters = element.Parameters
    break

filtered_parameter = [parameter.Definition.Name for parameter in all_parameters if parameter.IsReadOnly == False and parameter.StorageType == StorageType.String]

selected_parameter = forms.SelectFromList.show(sorted(filtered_parameter), title = "Select Parameters to Edit", width = 500, height = 800, multiselect = False)
if not selected_parameter:
    forms.alert("No Parameter Selected", title = "Script Exiting", warn_icon = True)
    script.exit()

prefix = forms.ask_for_string(
    default="",
    prompt="Enter Prefix - Blank if None",
    title=__title__
)

# Ensure prefix is not None
if prefix is None:
    prefix = ""

suffix = forms.ask_for_string(
    default="",
    prompt="Enter Suffix - Blank if None",
    title=__title__
)

# Ensure suffix is not None
if suffix is None:
    suffix = ""

content = forms.ask_for_string(
    default="",
    prompt="Enter Content - Blank if Default",
    title=__title__
)

t = Transaction(doc, "Bulk Param")
t.Start()

for element in target_elements:
    # Use LookupParameter with the selected parameter name
    parameter = element.LookupParameter(selected_parameter)
    
    if parameter:  # Ensure the parameter exists
        if not content:
            content = parameter.AsString()  # Retrieve the current value if content is blank
        
        # Ensure content is not None before concatenation
        if content is None:
            content = ""
        
        new_text = prefix + content + suffix
        parameter.Set(new_text)

t.Commit()

# forms.alert("Milestone Reached - Focus on WPF Forms", title = "Script Exiting", warn_icon = False)
