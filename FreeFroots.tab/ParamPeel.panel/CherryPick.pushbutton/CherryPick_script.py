# -*- coding: utf-8 -*-
'''CherryPick'''

__title__ = "CherryPick"
__author__ = "prakritisrimal"


from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import *
import xlrd
import clr
import clr
clr.AddReference("System")
clr.AddReference("System.Windows")
clr.AddReference("WindowsBase")
clr.AddReference("PresentationFramework")  # <-- Add this line
from System.Windows import Window          # <-- Now this works
from System import String, Array
from System.ComponentModel import INotifyPropertyChanged, PropertyChangedEventArgs
from System.Collections.ObjectModel import ObservableCollection
from pyrevit import script, UI, forms
import wpf
output = script.get_output()
ui_doc = __revit__.ActiveUIDocument
doc     = __revit__.ActiveUIDocument.Document # Get the Active Document
app     = __revit__.Application # Returns the Revit Application Object


# --- Plain Python Parameter class for WPF DataGrid binding ---


class Parameter(object):
    def __init__(self):
        self.IsSelected = False
        self.Name = ""
        self.ParameterType = None
        self.ParameterTypeOptions = Array[String](["Project Parameter", "Shared Parameter"])
        self.Discipline = None
        self.DisciplineOptions = Array[String](["Common", "Electrical", "Energy", "HVAC", "Infrastructure",
                                                "Piping", "Structural"])
        self.GroupUnder = None
        self.GroupUnderOptions = Array[String](["Analysis Results", "Analytical Alignment", "Analytical Model",
                                                "Constraints", "Construction", "Data","Dimensions","Division Geometry",
                                                "Electrical", "Electrical - Circuiting", "Electrical - Lighting",
                                                "Electrical - Loads", "Electrical Analysis", "Electrical Engineering",
                                                "Energy Analysis", "Fire Protection", "Forces", "General", "Graphics",
                                                "Green Building Properties", "Identity Data", "IFC Parameters", "Layers",
                                                "Life Safety", "Materials and Finishes", "Mechanical", "Mechanical - Flow",
                                                "Mechanical - Loads", "Model Properties", "Moments", "Other", "Overall Legend",
                                                "Phasing", "Photometrics", "Plumbing", "Rebar Set", "Releases / Member Forces",
                                                "Secondary End", "Segments and Fittings", "Set", "Slab Shape Edit",
                                                "Structural", "Structural Analysis", "Text", "Title Text", "Visibility"])
        self.InstanceOrType = None
        self.InstanceOrTypeOptions = Array[String](["Instance", "Type"])

# --- Main Window ---
class MainWindow(Window):
    def __init__(self):
        xaml_path = script.get_bundle_file("ui.xaml")
        wpf.LoadComponent(self, xaml_path)
        self.Parameters = []
        self.FilteredParameters = []
        self.Loaded += self.on_loaded

    # def on_loaded(self, sender, e):
    #     self.ParameterDataGrid = self.FindName("ParameterDataGrid")
    #     if self.ParameterDataGrid:
    #         self.ParameterDataGrid.ItemsSource = self.Parameters

    #     # Wire up checkbox events if present
    #     self.ShowOnlySharedCheckBox = self.FindName("ShowOnlySharedCheckBox")
    #     if self.ShowOnlySharedCheckBox:
    #         self.ShowOnlySharedCheckBox.Checked += self.ShowOnlySharedCheckBox_Checked
    #         self.ShowOnlySharedCheckBox.Unchecked += self.ShowOnlySharedCheckBox_Unchecked

    def on_loaded(self, sender, e):
        from Autodesk.Revit.DB import LabelUtils

        self.ParameterDataGrid = self.FindName("ParameterDataGrid")
        self.ParameterTypeFilterComboBox = self.FindName("ParameterTypeFilterComboBox")
        if self.ParameterTypeFilterComboBox:
            self.ParameterTypeFilterComboBox.SelectionChanged += self.ParameterTypeFilterComboBox_SelectionChanged

        if not self.ParameterDataGrid:
            return

        self.Parameters = []

        # Get all project parameters (including shared)
        param_bindings = doc.ParameterBindings
        it = param_bindings.ForwardIterator()
        it.Reset()
        while it.MoveNext():
            param_def = it.Key
            binding = it.Current

            p = Parameter()
            p.Name = param_def.Name

            # Parameter Type
            try:
                if hasattr(param_def, "IsShared") and param_def.IsShared:
                    p.ParameterType = "Shared Parameter"
                else:
                    p.ParameterType = "Project Parameter"
            except:
                p.ParameterType = "Project Parameter"

            # Group Under (Parameter Group)
            try:
                group = param_def.ParameterGroup
                group_name = LabelUtils.GetLabelFor(group)
                if group_name in p.GroupUnderOptions:
                    p.GroupUnder = group_name
                else:
                    p.GroupUnder = "Other"
            except:
                p.GroupUnder = "Other"

            # Discipline (best guess: use Group Under or default to "Common")
            if p.GroupUnder in p.DisciplineOptions:
                p.Discipline = p.GroupUnder
            else:
                p.Discipline = "Common"

            # Instance/Type
            try:
                if binding and binding.GetType().Name == "InstanceBinding":
                    p.InstanceOrType = "Instance"
                else:
                    p.InstanceOrType = "Type"
            except:
                p.InstanceOrType = "Instance"

            self.Parameters.append(p)

        # Sort by GroupUnder, then by InstanceOrType
        self.Parameters.sort(key=lambda p: (p.GroupUnder or "", p.InstanceOrType or ""))

        self.apply_parameter_type_filter()

        # Wire up checkbox events if present
        self.ShowOnlySharedCheckBox = self.FindName("ShowOnlySharedCheckBox")
        if self.ShowOnlySharedCheckBox:
            self.ShowOnlySharedCheckBox.Checked += self.ShowOnlySharedCheckBox_Checked
            self.ShowOnlySharedCheckBox.Unchecked += self.ShowOnlySharedCheckBox_Unchecked

    def apply_parameter_type_filter(self, *args):
        if hasattr(self, "ParameterTypeFilterComboBox") and self.ParameterTypeFilterComboBox:
            selected = self.ParameterTypeFilterComboBox.SelectedItem
            if selected is not None:
                filter_text = selected.Content
                if filter_text == "All":
                    self.FilteredParameters = self.Parameters
                else:
                    self.FilteredParameters = [p for p in self.Parameters if p.ParameterType == filter_text]
            else:
                self.FilteredParameters = self.Parameters
        else:
            self.FilteredParameters = self.Parameters

        self.ParameterDataGrid.ItemsSource = None
        self.ParameterDataGrid.ItemsSource = self.FilteredParameters

    def ParameterTypeFilterComboBox_SelectionChanged(self, sender, e):
        self.apply_parameter_type_filter()

    def AddParameter_Click(self, sender, e):
        self.Parameters.append(Parameter())
        self.ParameterDataGrid.ItemsSource = None
        self.ParameterDataGrid.ItemsSource = self.Parameters


    def ShowOnlySharedCheckBox_Checked(self, sender, e):
        for param in self.Parameters:
            param.ParameterTypeOptions = ["Shared Parameter"]
        self.ParameterDataGrid.ItemsSource = None
        self.ParameterDataGrid.ItemsSource = self.Parameters

    def ShowOnlySharedCheckBox_Unchecked(self, sender, e):
        for param in self.Parameters:
            param.ParameterTypeOptions = ["Project Parameter", "Shared Parameter"]
        self.ParameterDataGrid.ItemsSource = None
        self.ParameterDataGrid.ItemsSource = self.Parameters

window = MainWindow()
window.ShowDialog()
        
# class Parameter(INotifyPropertyChanged):
#     __events__ = ['PropertyChanged'] 
#     def __init__(self):
#         self._isSelected = False
#         self._name = ""
#         self._parameterType = None
#         self._discipline = None
#         self._groupUnder = None
#         self._instanceOrType = None

#     # .NET property for IsSelected
#     @property
#     def IsSelected(self):
#         return self._isSelected
#     @IsSelected.setter
#     def IsSelected(self, value):
#         self._isSelected = value
#         self.OnPropertyChanged("IsSelected")

#     @property
#     def Name(self):
#         return self._name
#     @Name.setter
#     def Name(self, value):
#         self._name = value
#         self.OnPropertyChanged("Name")

#     @property
#     def ParameterType(self):
#         return self._parameterType
#     @ParameterType.setter
#     def ParameterType(self, value):
#         self._parameterType = value
#         self.OnPropertyChanged("ParameterType")

#     @property
#     def ParameterTypeOptions(self):
#         # Return as .NET array for WPF
#         return Array[String](["Project Parameter", "Shared Parameter"])

#     @property
#     def Discipline(self):
#         return self._discipline
#     @Discipline.setter
#     def Discipline(self, value):
#         self._discipline = value
#         self.OnPropertyChanged("Discipline")

#     @property
#     def DisciplineOptions(self):
#         return Array[String](["Common", "Structural", "Mechanical", "Electrical"])

#     @property
#     def GroupUnder(self):
#         return self._groupUnder
#     @GroupUnder.setter
#     def GroupUnder(self, value):
#         self._groupUnder = value
#         self.OnPropertyChanged("GroupUnder")

#     @property
#     def GroupUnderOptions(self):
#         return Array[String](["Dimensions", "Identity Data", "Other"])

#     @property
#     def InstanceOrType(self):
#         return self._instanceOrType
#     @InstanceOrType.setter
#     def InstanceOrType(self, value):
#         self._instanceOrType = value
#         self.OnPropertyChanged("InstanceOrType")

#     @property
#     def InstanceOrTypeOptions(self):
#         return Array[String](["Instance", "Type"])

#     # INotifyPropertyChanged implementation
#     def OnPropertyChanged(self, propertyName):
#         if self.PropertyChanged:
#             self.PropertyChanged(self, PropertyChangedEventArgs(propertyName))


# class MainWindow(Window):
#     def __init__(self):
#         xaml_path = script.get_bundle_file("ui.xaml")
#         wpf.LoadComponent(self, xaml_path)
#         self.Parameters = []
#         self.Loaded += self.on_loaded

#     def on_loaded(self, sender, e):
#         self.ParameterDataGrid = self.FindName("ParameterDataGrid")
#         if self.ParameterDataGrid:
#             self.ParameterDataGrid.ItemsSource = self.Parameters

#     def AddParameter_Click(self, sender, e):
#         self.Parameters.append(Parameter())
#         # Manually refresh the DataGrid binding
#         self.ParameterDataGrid.ItemsSource = None
#         self.ParameterDataGrid.ItemsSource = self.Parameters

#     def ShowOnlySharedCheckBox_Checked(self, sender, e):
#         for param in self.Parameters:
#             param.ParameterTypeOptions = ["Shared Parameter"]
#         self.ParameterDataGrid.ItemsSource = None
#         self.ParameterDataGrid.ItemsSource = self.Parameters

#     def ShowOnlySharedCheckBox_Unchecked(self, sender, e):
#         for param in self.Parameters:
#             param.ParameterTypeOptions = ["Project Parameter", "Shared Parameter"]
#         self.ParameterDataGrid.ItemsSource = None
#         self.ParameterDataGrid.ItemsSource = self.Parameters

# # To show the window (uncomment if running as a standalone script in pyRevit)
# window = MainWindow()
# window.ShowDialog()

# # Function to extract categories and store them in a dictionary
# def get_all_categories(doc):
#     all_categories = {}
#     for category in doc.Settings.Categories:
#         if hasattr(category, "BuiltInCategory") and category.BuiltInCategory != BuiltInCategory.INVALID:
#             all_categories[category.Name] = category.BuiltInCategory
#     return all_categories

# # Function to generate a CategorySet from a list of category names
# # and a mapping of category names to BuiltInCategory
# def generate_category_set(categories, category_map):
#     category_set = app.Create.NewCategorySet()
#     for category_name in categories:
#         built_in_category = category_map.get(category_name.strip())
#         if built_in_category:
#             main_category = Category.GetCategory(doc, built_in_category)
#             if main_category:
#                 category_set.Insert(main_category)
#                 # Check and insert only valid model subcategories
#                 if main_category.SubCategories:
#                     for sub_category in main_category.SubCategories:
#                         if sub_category.CategoryType == CategoryType.Model: 
#                             if sub_category.AllowsBoundParameters:
#                                 category_set.Insert(sub_category)

#     return category_set

# # Function to get parameter groups and their user-friendly names
# # from the BuiltInParameterGroup enumeration
# def get_parameter_groups(doc):
#     param_groups = {}
#     for group in BuiltInParameterGroup.GetValues(BuiltInParameterGroup):
#         group_name = LabelUtils.GetLabelFor(group)  # Get user-friendly name
#         if group_name:
#             param_groups[group_name] = group
#     return param_groups


# user_choice = forms.alert("This Tool helps you Manage Shared Parameters",
#                                 title="Shared Parameters - Select Option", 
#                                 warn_icon=False, 
#                                 options=["Add Shared Parameters", "Remove Shared Parameters"])

# if not user_choice:
#     script.exit()


# if user_choice == "Add Shared Parameters": 

#     # Ask user to select shared parameter file
#     txt_file = forms.alert("Select Shared Parameter.txt File", warn_icon= False)
#     if not txt_file:
#         script.exit()
#     # Check if the file is a valid shared parameter file
#     param_file_path = forms.pick_file(file_ext='txt')
#     if not param_file_path:
#         script.exit()
        
#     # Check if the file is a valid shared parameter file
#     app.SharedParametersFilename = param_file_path
#     shared_param_file = app.OpenSharedParameterFile()
#     if not shared_param_file:
#         forms.alert("Shared Parameter File not found.")
#         script.exit()

#     # Sort all Parameters from SharedParameterFile
#     available_params = {}
#     all_parameter_names = []
#     for group in shared_param_file.Groups:
#         for defn in group.Definitions:
#             all_parameter_names.append(defn.Name)

#     #Ask user to select shared parameters to be added
#     user_selected_names = forms.SelectFromList.show(sorted(all_parameter_names), multiselect = True, title = "Select Shared Parameters that need to be added")
#     for group in shared_param_file.Groups:
#         for defn in group.Definitions:
#             if defn.Name in user_selected_names:
#                 key = '[{}]_{}'.format(group.Name, defn.Name)
#                 available_params[key] = defn


# # Extract categories for mapping
# category_map = get_all_categories(doc)
# param_groups_dict = get_parameter_groups(doc)

# # Read Excel file
# xlsx_file = forms.alert("Select the Excel.xlsx File", warn_icon=False)
# if not xlsx_file:
#     script.exit()
# # Check if the file is a valid Excel file
# excel_path = forms.pick_excel_file()
# if not excel_path:
#     script.exit()
# workbook = xlrd.open_workbook(excel_path)
# sheet = workbook.sheet_by_index(0)

# param_collector = FilteredElementCollector(doc).OfClass(SharedParameterElement)

# # Find if the shared parameter already exists in the revit model
# existing_params = []
# existing_names = []
# for parameter in param_collector:
#     if user_choice == "Add Shared Parameters":
#         if parameter.Name in user_selected_names:
#             existing_params.append(parameter)
#             existing_names.append(parameter.Name)
#     else: 
#         existing_params.append(parameter)
#         existing_names.append(parameter.Name)

# # Parse Excel data
# entries = []
# for i in range(1, sheet.nrows):  # Skip header row
#     group = sheet.cell_value(i, 0)
#     parameter_name = sheet.cell_value(i, 1)
#     if user_choice == "Add Shared Parameters":
#         if parameter_name in user_selected_names:
#             categories = sheet.cell_value(i, 2).split(',')
#             categories = [cat.strip().title() for cat in categories]
#             paramtype = sheet.cell_value(i, 3)
#             paramgroup = sheet.cell_value(i, 4)
#             key = '[{}]_{}'.format(group, parameter_name)
#             entries.append((key, parameter_name, categories, paramtype, paramgroup))
#     else:
#         categories = sheet.cell_value(i, 2).split(',')
#         categories = [cat.strip().title() for cat in categories]
#         paramtype = sheet.cell_value(i, 3)
#         paramgroup = sheet.cell_value(i, 4)
#         key = '[{}]_{}'.format(group, parameter_name)
#         entries.append((key, parameter_name, categories, paramtype, paramgroup))

# added, skipped, updated, removed = [], [], [], []


# try:
#     action = "Add" if user_choice == "Add Shared Parameters" else "Remove"
#     txn = Transaction(doc,"{} Shared Parameters", format(action))
#     txn.Start()

#     for key, parameter_name, catlist, paramtype, paramgroup in entries:
#         group_enum = param_groups_dict.get(paramgroup)
#         executed =  False

#         #Check if the parameter already exists in the model
#         bind_map = doc.ParameterBindings
#         it = bind_map.Forwardit()
#         it.Reset()
#         while it.MoveNext():
#             paramdef = it.Key
#             # Check if the parameter is already bound to the model
#             if paramdef.Name in existing_names:
#                 binding = it.Current
#                 if paramdef.Name == parameter_name:
#                     existing_cats = [cat.Name for cat in binding.Categories]

#                     # Compare with Excel categories
#                     missing_categories = [cat for cat in existing_cats if cat not in categories]
#                     new_cats = [cat for cat in catlist if cat not in existing_cats]
            
#                     if new_cats:
#                         updated_catset = generate_category_set(catlist, category_map)
#                         new_bind = app.Create.NewInstanceBinding(updated_catset) if paramtype.lower() == "instance" else app.Create.NewTypeBinding(updated_catset)

#                         try:
#                             doc.ParameterBindings.ReInsert(paramdef, new_bind, paramgroup)
#                             updated.append([parameter_name, catlist])
#                             executed = True
#                             break
#                         except Exception as e:
#                             skipped.append([parameter_name, "UNABLE TO UPDATE: {}".format(e)])
                

#         if user_choice == "Add Shared Parameters" and not executed:
#             defn = available_params.get(key)
#             if defn:
#                 c_set = generate_category_set(catlist, category_map)
                
#                 if c_set.Size > 0:
#                     binding = app.Create.NewInstanceBinding(c_set) if paramtype.lower() == "instance" else app.Create.NewTypeBinding(c_set)

#                     try:
#                         doc.ParameterBindings.Insert(defn, binding, paramgroup)
#                         added.append([defn.Name, catlist])
#                     except Exception as e:
#                         skipped.append([defn.Name, "FAILED TO ADD PARAMETER: {}".format(e)])
#                         pass
#                 else:
#                     skipped.append([parameter_name, "CATEGORIES MISMATCH"])
#             else:
#                 skipped.append([parameter_name, "PARAMETER MISSING"])


#         elif user_choice == "Remove Shared Parameters" and parameter_name in existing_names:
#             #Find existing categories and bindings
#             bind_map = doc.ParameterBindings
#             it = bind_map.Forwardit()
#             it.Reset()
#             while it.MoveNext():
#                 paramdef = it.Key
#                 binding = it.Current
#                 if paramdef.Name == parameter_name:
#                     existing_cats = [cat.Name for cat in binding.Categories]
#                     # Check if the parameter is bound to any categories
#                     if any(cat in existing_cats for cat in catlist):
#                         try:
#                             # Unbind and remove parameter
#                             doc.ParameterBindings.Remove(paramdef)
#                             removed.append([parameter_name, catlist])
#                             break
#                         except Exception as e:
#                             skipped.append([parameter_name, "FAILED TO REMOVE PARAMETER : {}".format(e)])
#                     else:
#                         skipped.append([parameter_name, "CATEGORIES DO NOT MATCH"])
#                         break
#         else:
#             skipped.append([parameter_name, "PARAMETER NOT FOUND"])
#     txn.Commit()


# except Exception as e:
#     forms.alert("An error occurred: {}".format(e))


# if added:
#     output.print_md("##⚠️ {} Completed.😊 ".format(__title__))
#     output.print_md("---")
#     output.print_md("✅ Shared Parameters Added. Refer to the **Table Report** below for reference")
#     output.print_table(table_data=added, columns=["PARAMETER NAME", "CATEGORIES"])
#     output.print_md("---")

# if updated:
#     output.print_md("##⚠️ {} Updated.😊 ".format(__title__))
#     output.print_md("---")
#     output.print_md("✅ Shared Parameters Updated. Refer to the **Table Report** below for reference")
#     output.print_table(table_data=updated, columns=["PARAMETER NAME", "CATEGORIES"])
#     output.print_md("---")

# if skipped:
#     output.print_md("##⚠️ {} Completed. Issues Found ☹️".format(__title__))
#     output.print_md("---")
#     output.print_md("❌ Some Shared Parameters were not added. Refer to the **Table Report** below for reference")
#     output.print_table(table_data=skipped, columns=["PARAMETER NAME","ERROR CODE"])
#     output.print_md("---")
#     output.print_md("***✅ ERROR CODE REFERENCE***")
#     output.print_md("---")
#     output.print_md("**FAILED TO ADD PARAMETER** - Unable to add Shared Parameter. Add manually. \n")
#     output.print_md("**CATEGORIES MISMATCH** - Model Categories not found to add the Shared Parameter. \n")
#     output.print_md("**PARAMETER MISSING** - Shared Parameter not found in .txt file \n")
#     output.print_md("---")

# if removed:
#     output.print_md("##⚠️ " + __title__ + " Completed.😊")
#     output.print_md("---")
#     output.print_md("🗑️ Shared Parameters Removed. Refer to the **Table Report** below for reference")
#     output.print_table(table_data=removed, columns=["PARAMETER NAME", "CATEGORIES"])
#     output.print_md("---")












    

















    




