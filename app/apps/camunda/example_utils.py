from utils import get_form_details, get_form_details_old, get_forms

# This is an example of how to map a form to a dictionary
html_form = """
<form name="generatedForm" role="form">
  <div class="form-group">
    <label for="situation">
      Wat is de situatie?
    </label>
    <input class="form-control" name="situation" cam-variable-type="String" cam-variable-name="situation" type="text" />
    <div ng-if="this.generatedForm.situation.$invalid && this.generatedForm.situation.$dirty" class="has-error">
      <div ng-show="this.generatedForm.situation.$error.required" class="help-block">
        Required field
      </div>
      <div ng-show="this.generatedForm.situation.$error.camVariableType" class="help-block">
        Only a string value is allowed
      </div>
    </div>
  </div>
  <div class="form-group">
    <label for="can_next_visit_go_ahead">
      Kan volgende bezoek doorgaan?
    </label>
    <input class="form-control" name="can_next_visit_go_ahead" cam-variable-type="Boolean" cam-variable-name="can_next_visit_go_ahead" type="checkbox" />
    <div ng-if="this.generatedForm.can_next_visit_go_ahead.$invalid && this.generatedForm.can_next_visit_go_ahead.$dirty" class="has-error">
      <div ng-show="this.generatedForm.can_next_visit_go_ahead.$error.required" class="help-block">
        Required field
      </div>
      <div ng-show="this.generatedForm.can_next_visit_go_ahead.$error.camVariableType" class="help-block">
        Only a boolean value is allowed
      </div>
    </div>
  </div>
  <div class="form-group">
    <label for="FormField_3qjm0em">
      LABEL 0
    </label>
    <select class="form-control" name="FormField_3qjm0em" cam-variable-type="String" cam-variable-name="FormField_3qjm0em">
      <option value="Value_0iaq2tn">
        test
      </option>
      <option value="Value_0qd0jvv">
        asffassfa
      </option>
    </select>
    <div ng-if="this.generatedForm.FormField_3qjm0em.$invalid && this.generatedForm.FormField_3qjm0em.$dirty" class="has-error">
      <div ng-show="this.generatedForm.FormField_3qjm0em.$error.required" class="help-block">
        Required field
      </div>
      <div ng-show="this.generatedForm.FormField_3qjm0em.$error.camVariableType" class="help-block">
        Only a string value is allowed
      </div>
    </div>
  </div>
  <div class="form-group">
    <label for="FormField_3vj52a2">
      LABEL 1
    </label>
    <div class="input-group">
      <input class="form-control" name="FormField_3vj52a2" cam-variable-type="String" cam-variable-name="FormField_3vj52a2" type="text" uib-datepicker-popup="dd/MM/yyyy" is-open="dateFieldOpenedFormField_3vj52a2" />
      <div class="input-group-btn">
        <button type="button" class="btn btn-default" ng-click="openFormField_3vj52a2($event)">
          <i class="glyphicon glyphicon-calendar"></i>
        </button>
      </div>
      <script cam-script type="text/form-script">
        $scope.openFormField_3vj52a2 = function ($event) { $event.preventDefault(); $event.stopPropagation(); $scope.dateFieldOpenedFormField_3vj52a2 = true; };
      </script>
    </div>
    <div ng-if="this.generatedForm.FormField_3vj52a2.$invalid && this.generatedForm.FormField_3vj52a2.$dirty" class="has-error">
      <div ng-show="this.generatedForm.FormField_3vj52a2.$error.required && !this.generatedForm.FormField_3vj52a2.$error.date" class="help-block">
        Required field
      </div>
      <div ng-show="this.generatedForm.FormField_3vj52a2.$error.date" class="help-block">
        Invalid date format: the date should have the pattern 'dd/MM/yyyy'
      </div>
    </div>
  </div>
  <div class="form-group">
    <label for="FormField_0cgfa15">
      LABEL 3
    </label>
    <input class="form-control" name="FormField_0cgfa15" cam-variable-type="Long" cam-variable-name="FormField_0cgfa15" type="text" />
    <div ng-if="this.generatedForm.FormField_0cgfa15.$invalid && this.generatedForm.FormField_0cgfa15.$dirty" class="has-error">
      <div ng-show="this.generatedForm.FormField_0cgfa15.$error.required" class="help-block">
        Required field
      </div>
      <div ng-show="this.generatedForm.FormField_0cgfa15.$error.camVariableType" class="help-block">
        Only a long value is allowed
      </div>
    </div>
  </div>
</form>"""

forms = get_forms(html_form)
form = forms[0]

form_details_old = get_form_details_old(form)
form_details = get_form_details(form)

print(form_details_old)
print(form_details)

# Should return something like:
# {
#     "inputs": [
#         {
#             "type": "text",
#             "camunda_type": "String",
#             "name": "situation",
#             "default_value": "",
#             "label": "Wat is de situatie?",
#             "required": True,
#             "is_date": False,
#         },
#         {
#             "type": "checkbox",
#             "camunda_type": "Boolean",
#             "name": "can_next_visit_go_ahead",
#             "default_value": "",
#             "label": "Kan volgende bezoek doorgaan?",
#             "required": True,
#             "is_date": False,
#         },
#         {
#             "type": "text",
#             "camunda_type": "String",
#             "name": "FormField_3vj52a2",
#             "default_value": "",
#             "label": "LABEL 1",
#             "required": False,
#             "is_date": True,
#         },
#         {
#             "type": "text",
#             "camunda_type": "Long",
#             "name": "FormField_0cgfa15",
#             "default_value": "",
#             "label": "LABEL 3",
#             "required": True,
#             "is_date": False,
#         },
#     ]
# }


# EXAMPLE NEW
# [
#   {
#     "camunda_task_id": "b58b7313-7a1c-11eb-9cc4-0242ac120008",
#     "task_name_id": "task_create_visit",
#     "name": "Doorgeven huisbezoek resultaat",
#     "due_date": "2021-04-30T00:28:48.842+0200",
#     "roles": ["Toezichthouder"],
#     "form": [
#       {
#         "label": "Wat is de situatie?",
#         "type": "text",
#         "camunda-type": "String",
#         "name": "situation",
#         "default_value": "",
#         "required": true,
#         "is_date": false,
#         "options": null
#       },
#       {
#         "label": "Kan volgende bezoek doorgaan?",
#         "type": "checkbox",
#         "camunda-type": "Boolean",
#         "name": "can_next_visit_go_ahead",
#         "default_value": "true",
#         "required": true,
#         "is_date": false,
#         "options": null
#       }
#     ],
#     "render_form": "<form name=\"generatedForm\" role=\"form\">\n  <div class=\"form-group\">\n    <label for=\"situation\">\n      Wat is de situatie?\n    </label>\n    <input class=\"form-control\" name=\"situation\" cam-variable-type=\"String\" cam-variable-name=\"situation\" type=\"text\" />\n    <div ng-if=\"this.generatedForm.situation.$invalid && this.generatedForm.situation.$dirty\" class=\"has-error\">\n      <div ng-show=\"this.generatedForm.situation.$error.required\" class=\"help-block\">\n        Required field\n      </div>\n      <div ng-show=\"this.generatedForm.situation.$error.camVariableType\" class=\"help-block\">\n        Only a string value is allowed\n      </div>\n    </div>\n  </div>\n  <div class=\"form-group\">\n    <label for=\"can_next_visit_go_ahead\">\n      Kan volgende bezoek doorgaan?\n    </label>\n    <input class=\"form-control\" name=\"can_next_visit_go_ahead\" cam-variable-type=\"Boolean\" cam-variable-name=\"can_next_visit_go_ahead\" type=\"checkbox\" value=\"true\" />\n    <div ng-if=\"this.generatedForm.can_next_visit_go_ahead.$invalid && this.generatedForm.can_next_visit_go_ahead.$dirty\" class=\"has-error\">\n      <div ng-show=\"this.generatedForm.can_next_visit_go_ahead.$error.required\" class=\"help-block\">\n        Required field\n      </div>\n      <div ng-show=\"this.generatedForm.can_next_visit_go_ahead.$error.camVariableType\" class=\"help-block\">\n        Only a boolean value is allowed\n      </div>\n    </div>\n  </div>\n</form>\n",
#     "form_variables": {
#       "can_next_visit_go_ahead": {
#         "type": "Boolean",
#         "value": true,
#         "valueInfo": {}
#       },
#       "case_identification": {
#         "type": "String",
#         "value": "1ca6de23-a03b-41b7-a81a-376c9887df05",
#         "valueInfo": {}
#       },
#       "zaken_access_token": {
#         "type": "String",
#         "value": "CAMUNDA_SECRET_KEY",
#         "valueInfo": {}
#       },
#       "zaken_state_endpoint": {
#         "type": "String",
#         "value": "http://zaak-gateway:8000/api/v1/camunda/worker/state/",
#         "valueInfo": {}
#       },
#       "situation": { "type": "String", "value": null, "valueInfo": {} }
#     }
#   }
# ]
