from python_terraform import Terraform


def deploy():
    tf = Terraform(working_dir='infrastructure')
    tf.init()
    tf.apply(skip_plan=True)


if __name__ == '__main__':
    deploy()
