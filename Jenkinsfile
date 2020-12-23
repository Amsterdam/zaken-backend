#!groovy

def tag_image_as(docker_image_url, tag) {
  // tag image, push to repo, remove local tagged image
  script {
    docker.image("${docker_image_url}:${env.COMMIT_HASH}").push(tag)
    sh "docker rmi ${docker_image_url}:${tag} || true"
  }
}

def deploy(app_name, environment) {
  build job: 'Subtask_Openstack_Playbook',
    parameters: [
        [$class: 'StringParameterValue', name: 'INVENTORY', value: environment],
        [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy.yml'],
        [$class: 'StringParameterValue', name: 'PLAYBOOKPARAMS', value: "-e cmdb_id=app_${app_name}"],
    ]
}

def build_image(docker_image_url, source) {
  script {
    def image = docker.build("${docker_image_url}:${env.COMMIT_HASH}",
      "--no-cache " +
      "--shm-size 1G " +
      "--build-arg COMMIT_HASH=${env.COMMIT_HASH} " +
      "--build-arg BRANCH_NAME=${env.BRANCH_NAME} " +
      " ${source}")
    image.push()
    tag_image_as(docker_image_url, "latest")
  }
}

def remove_image(docker_image_url) {
    // delete original image built on the build server
    sh "docker rmi ${docker_image_url}:${env.COMMIT_HASH} || true"
}

pipeline {
  agent any
  environment {

    APPS = [
      [name: "zaken", docker_image_url: "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken", source: "./app"]
      [name: "zaken-camunda", docker_image_url: "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken-camunda", source: "./camunda"]
    ]
  }

  stages {
    stage("Checkout") {
      steps {
        checkout scm
        script {
          env.COMMIT_HASH = sh(returnStdout: true, script: "git log -n 1 --pretty=format:'%h'").trim()
        }
      }
    }

    stage("Build docker images") {
      steps {
        env.APPS.each { app ->
          build_image(app.docker_image_url, app.source)
        }
      }
    }

    stage("Push and deploy acceptance images") {
      when {
        not { buildingTag() }
        branch 'master'
      }
      steps {
        env.APPS.each { app ->
          tag_image_as(app.docker_image_url, "acceptance")
          deploy(app.name, "acceptance")
        }
      }
    }

    stage("Push and deploy production images") {
      when { buildingTag() }
      steps {
        env.APPS.each { app ->
          tag_image_as(app.docker_image_url, "production")
          deploy(app.name, "production")
        }
      }
    }
  }

  post {
    always {
      script {
        env.APPS.each { app ->
          remove_image(app.docker_image_url)
        }
      }
    }
  }
}
