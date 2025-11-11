from rx.config import RunConfig, GlobalContext
from rx.helper.dockercli_helper import dockercli_login


def handle_dockerhub_image_publish(run_cfg: RunConfig, ctx: GlobalContext):
    """
    Publish Docker image to Docker Hub
    1. docker login
    2. docker tag
    3. docker push
    4. docker logout
    5. cleanup local image if needed

    :param run_cfg:
    :param ctx:
    :return:
    """
    src = run_cfg.src
    dest = run_cfg.dest


default_actions = {
    "publish-image": {
        "src": "${{vars.IMAGE_NAME}}:${{vars.IMAGE_TAG}}",
        "dest": "dockerhub://${{env.DOCKERHUB_USERNAME}}/${{env.DOCKERHUB_TOKEN}}:${{vars.IMAGE_TAG}}",
    },
}
