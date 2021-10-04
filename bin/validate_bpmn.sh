cd app
for filename in apps/workflow/bpmn_files/**/**/**/*.bpmn; do
        bpmnlint "$filename"
done
