#!groovy

// tag image, push to repo, remove local tagged image
def tag_image_as(tag, docker_image_url) {
  script {
    docker.image("${docker_image_url}:${env.COMMIT_HASH}").push(tag)
    sh "docker rmi ${docker_image_url}:${tag} || true"
  }
}

def deploy(environment, app) {
  build job: 'Subtask_Openstack_Playbook',
    parameters: [
        [$class: 'StringParameterValue', name: 'INVENTORY', value: environment],
        [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy.yml'],
        [$class: 'StringParameterValue', name: 'PLAYBOOKPARAMS', value: "-e cmdb_id=app_${app}"],
    ]
}

def build_image(docker_image_url, src) {
  script {
    def image = docker.build("${docker_image_url}:${env.COMMIT_HASH}",
      "--no-cache " +
      "--shm-size 1G " +
      "--build-arg COMMIT_HASH=${env.COMMIT_HASH} " +
      "--build-arg BRANCH_NAME=${env.BRANCH_NAME} " +
      " ${src}")
    image.push()
    tag_image_as("latest", docker_image_url)
  }
}

def remove_image(docker_image_url) {
    // delete original image built on the build server
    sh "docker rmi ${docker_image_url}:${env.COMMIT_HASH} || true"
}

pipeline {
  agent any
  environment {
    APP = "zaken"
    DOCKER_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken"

    APP_CAMUNDA = "zaken-camunda"
    CAMUNDA_DOCKER_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken-camunda"
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

    stage("Build docker image") {
      steps {
        build_image(DOCKER_IMAGE_URL, "./app")
        build_image(CAMUNDA_DOCKER_IMAGE_URL, "./camunda")
      }
    }

    stage("Push and deploy acceptance image") {
      when {
        not { buildingTag() }
        branch 'master'
      }
      steps {
        tag_image_as("acceptance", env.APP)
        deploy("acceptance", env.APP)

        tag_image_as("acceptance", env.APP)
        deploy("acceptance", env.APP_CAMUNDA)
      }
    }

    stage("Push and deploy production image") {
      when { buildingTag() }
      steps {
        tag_image_as("production", env.APP)
        deploy("production", env.APP)

        tag_image_as("production", env.APP_CAMUNDA)
        deploy("production", env.APP_CAMUNDA)
      }
    }
  }

  post {
    always {
      script {
        remove_image(env.DOCKER_IMAGE_URL)
        remove_image(env.CAMUNDA_DOCKER_IMAGE_URL)
      }
    }
  }
}
