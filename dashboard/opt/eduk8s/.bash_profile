# Enable kubectl bash completion.

source <(kubectl completion bash)

# Enable oc bash completion.

source <(oc completion bash)

# Source profile provided for the workshop.

if [ -f /opt/eduk8s/workshop/profile ]; then
    source /opt/eduk8s/workshop/profile
fi

if [ -f $HOME/workshop/profile ]; then
    source $HOME/workshop/profile
fi

# Source $HOME/.bashrc profile in case used.

if [ -f $HOME/.bashrc ]; then
    source $HOME/.bashrc
fi
