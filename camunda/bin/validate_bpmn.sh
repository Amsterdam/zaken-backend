cd camunda

for filename in BPMN/*.bpmn; do
        bpmnlint "$filename"
done
