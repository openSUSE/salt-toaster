# Salt-toaster pipelines

Welcome to salt-toaster jenkins pipelines!

## Currently workflow

Currently you need to create manual the jenkins job and configure as pipeline.
Then you can say to the jenkins job to pull the code from here.
This manual configuration is only needed by first iteration, once you create the pipeline that will take the code from this repo, everytime you push code here, the pipeline will use latest code from pipeline.

We might add in future the jenkins-builder plugin for creating the pipeline automatically.

## Creating new pipelines.

As you can see for creating new pipelines the pattern is really simple.

If you want to create for sle15 pipelines or other OS version, just change the variable and you are ready to go !