for filename in app/apps/workflow/bpmn_files/**/**/**/*.bpmn; do
        bpmnlint "$filename"
done
