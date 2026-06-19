"""Shell integration hooks."""

ZSH_HOOK = r'''
# awsctx shell integration
awsctx() {
    local output
    output="$(command awsctx "$@")"
    local exit_code=$?
    if [[ $exit_code -eq 0 && -n "$output" ]]; then
        local profile region
        profile="$(echo "$output" | sed -n '1p')"
        region="$(echo "$output" | sed -n '2p')"
        export AWS_PROFILE="$profile"
        export AWS_DEFAULT_REGION="$region"
        # Print the display lines (everything after line 2)
        echo "$output" | tail -n +3
    fi
}
'''

BASH_HOOK = r'''
# awsctx shell integration
awsctx() {
    local output
    output="$(command awsctx "$@")"
    local exit_code=$?
    if [[ $exit_code -eq 0 && -n "$output" ]]; then
        local profile region
        profile="$(echo "$output" | sed -n '1p')"
        region="$(echo "$output" | sed -n '2p')"
        export AWS_PROFILE="$profile"
        export AWS_DEFAULT_REGION="$region"
        echo "$output" | tail -n +3
    fi
}
'''

FISH_HOOK = r'''
# awsctx shell integration
function awsctx
    set -l output (command awsctx $argv)
    set -l exit_code $status
    if test $exit_code -eq 0 -a -n "$output"
        set -gx AWS_PROFILE $output[1]
        set -gx AWS_DEFAULT_REGION $output[2]
        for line in $output[3..]
            echo $line
        end
    end
end
'''


def get_shell_hook(shell: str) -> str:
    hooks = {
        "zsh": ZSH_HOOK,
        "bash": BASH_HOOK,
        "fish": FISH_HOOK,
    }
    if shell not in hooks:
        raise ValueError(f"Unsupported shell: {shell}. Supported: {', '.join(hooks.keys())}")
    return hooks[shell].strip()
