#!groovy

def tag_image_as(docker_image_url, tag) {
  // Tag image, push to repo, remove local tagged image
  script {
    docker.image("${docker_image_url}:${env.COMMIT_HASH}").push(tag)
    sh "docker rmi ${docker_image_url}:${tag} || true"
  }
}

def deploy(app_name, environment) {
  // Deploys the app to the given environment
  build job: 'Subtask_Openstack_Playbook',
    parameters: [
        [$class: 'StringParameterValue', name: 'INVENTORY', value: environment],
        [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy.yml'],
        [$class: 'StringParameterValue', name: 'PLAYBOOKPARAMS', value: "-e cmdb_id=app_${app_name}"],
    ]
}

def tag_and_deploy(docker_image_url, app_name, environment) {
  // Tags the Docker with the environment, en deploys to the same environment
  script {
    tag_image_as(docker_image_url, environment)
    deploy(app_name, environment)
  }
}

def build_image(docker_image_url, source) {
  // Builds the image given the source, and pushes it to the Amsterdam Docker registry
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
    script {
      sh "docker rmi ${docker_image_url}:${env.COMMIT_HASH} || true"
    }
}

pipeline {
  agent any
  environment {
    PRODUCTION = "production"
    ACCEPTANCE = "acceptance"

    ZAKEN_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken"
    ZAKEN_SOURCE = "./app"
    ZAKEN_NAME = "zaken"

    CAMUNDA_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken-camunda"
    CAMUNDA_SOURCE = "./camunda"
    CAMUNDA_NAME = "zaken-camunda"

    REDIS_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken-redis"
    REDIS_SOURCE = "./redis"
    REDIS_NAME = "zaken-redis"

    OPEN_ZAAK_IMAGE_URL = "${DOCKER_REGISTRY_NO_PROTOCOL}/fixxx/zaken-open-zaak"
    OPEN_ZAAK_SOURCE = "./open-zaak"
    OPEN_ZAAK_NAME = "zaken-open-zaak"

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
        build_image(env.ZAKEN_IMAGE_URL, env.ZAKEN_SOURCE)
        // build_image(env.CAMUNDA_IMAGE_URL, env.CAMUNDA_SOURCE)
        // build_image(env.REDIS_IMAGE_URL, env.REDIS_SOURCE)
        // build_image(env.OPEN_ZAAK_IMAGE_URL, env.OPEN_ZAAK_SOURCE)
      }
    }

    stage("Push and deploy acceptance images") {
      when {
        not { buildingTag() }
        branch 'master'
      }
      steps {
        // tag_and_deploy(env.OPEN_ZAAK_IMAGE_URL, env.OPEN_ZAAK_NAME, env.ACCEPTANCE)
        // tag_and_deploy(env.REDIS_IMAGE_URL, env.REDIS_NAME, env.ACCEPTANCE)
        // tag_and_deploy(env.CAMUNDA_IMAGE_URL, env.CAMUNDA_NAME, env.ACCEPTANCE)
        tag_and_deploy(env.ZAKEN_IMAGE_URL, env.ZAKEN_NAME, env.ACCEPTANCE)
      }
    }

    stage("Push and deploy production images") {
      // Only deploy to production if there is a tag
      when { buildingTag() }
      steps {
        tag_and_deploy(env.OPEN_ZAAK_IMAGE_URL, env.OPEN_ZAAK_NAME, env.PRODUCTION)
        tag_and_deploy(env.REDIS_IMAGE_URL, env.REDIS_NAME, env.PRODUCTION)
        tag_and_deploy(env.CAMUNDA_IMAGE_URL, env.CAMUNDA_NAME, env.PRODUCTION)
        tag_and_deploy(env.ZAKEN_IMAGE_URL, env.ZAKEN_NAME, env.PRODUCTION)
      }
    }
  }

  post {
    always {
        remove_image(env.ZAKEN_IMAGE_URL)
        // remove_image(env.CAMUNDA_IMAGE_URL)
        // remove_image(env.REDIS_IMAGE_URL)
        // remove_image(env.OPEN_ZAAK_IMAGE_URL)
    }
  }
}
