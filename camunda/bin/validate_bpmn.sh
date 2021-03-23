apt-get install -y npm
npm install bpmnlint

for filename in BPMN/*.bpmn; do
        bpmnlint "$filename"
    done
done
