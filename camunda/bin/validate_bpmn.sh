cd camunda

for filename in build/resources/main/bpmn/*.bpmn; do
        bpmnlint "$filename"
done
