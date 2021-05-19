cd camunda

for filename in src/main/resources/bpmn/*.bpmn; do
        bpmnlint "$filename"
done
