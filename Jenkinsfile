#!groovy

def tag_image_as(docker_image_url, tag) {
  // tag image, push to repo, remove local tagged image
  script {
    docker.image("${docker_image_url}:${env.COMMIT_HASH}").push(tag)
    sh "docker rmi ${docker_image_url}:${tag} || true"
  }
}

def deploy(app, environment) {
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
        build_image(env.DOCKER_IMAGE_URL, "./app")
        build_image(env.CAMUNDA_DOCKER_IMAGE_URL, "./camunda")
      }
    }

    stage("Push and deploy acceptance image") {
      when {
        not { buildingTag() }
        branch 'master'
      }
      steps {
        tag_image_as(env.DOCKER_IMAGE_URL, "acceptance")
        deploy(env.APP, "acceptance")

        tag_image_as(env.CAMUNDA_DOCKER_IMAGE_URL, "acceptance")
        deploy(env.APP_CAMUNDA, "acceptance", )
      }
    }

    stage("Push and deploy production image") {
      when { buildingTag() }
      steps {
        tag_image_as(env.DOCKER_IMAGE_URL, "production")
        deploy(env.APP, "production")

        tag_image_as(env.CAMUNDA_DOCKER_IMAGE_URL, "production")
        deploy(env.APP_CAMUNDA, "production")
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
