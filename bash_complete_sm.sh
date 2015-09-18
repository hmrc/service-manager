# Servicce manager bash completion
#
# See https://github.com/hmrc/service-manager
#
# Restriction : currently gets service names from default location; ignores the -c/--config option for completion
# #################################################################################################################
_sm_get_last_arg () 
{ 
    local i;
    arg=;
    for ((i=COMP_CWORD-1; i >= 0; i-- ))
    do
        if [[ "${COMP_WORDS[i]}" == -* ]]; then
            arg=${COMP_WORDS[i]};
            break;
        fi;
    done
}
_sm_get_config () 
{
	local i;
    config=;
    for ((i=1; i < COMP_CWORD; i++ ))
    do
        if [[ "${COMP_WORDS[i]}" == "-c" || "${COMP_WORDS[i]}" == "--config" ]]; then
            config="-c ${COMP_WORDS[i+1]}";
            break;
        fi;
    done
}
_sm()
{
	local cur immedprev otherprev opts
	COMPREPY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	immedprev="${COMP_WORDS[COMP_CWORD-1]}"
	_sm_get_last_arg
	otherprev=$arg
	mmopts="--appendArgs --autorefresh --checkports --cleanlogs --config --describe --fatjar --feature --getdascode --info --help --logs --noprogress --offine"
	mmopts="$mmopts --ports --port --printconfig --proxy --pullall --release --restart --showcmdfor --shownotrunning --start --status --stop --wait"
	mopts="-c -d -f -F -h -i -l -n -o -r -s -w"

	# Single value for the argument
	case "${immedprev}" in
		-c|--config)
			COMPREPLY=( $(compgen -f ${cur}) )
			return 0
			;;
		--proxy|-F|--feature|--appendArgs|-w|--wait|--port)
			return 0
			;;
	esac

	# Potentially multiple values for the argument
	case "${otherprev}" in
		--start|--stop|--restart|--logs|-l|--status|-s|--autorefresh|--printconfig|--getdascode|--showcmdfor)
			_sm_get_config
			# local svcs="SACA_DEP SACA_ALL SA_APPEALS_FRONTEND"
			local svcs=`sm -d $config | awk -F '=' '{print $1}' | grep -v 'Services:'  | xargs`
			COMPREPLY=( $(compgen -W "${svcs}" -- ${cur}) )
			return 0
			;;
	esac


	if [[ ${cur} == --* ]] ; then
		COMPREPLY=( $(compgen -W "${mmopts}" -- ${cur}) )
		return 0
	fi

	if [[ ${cur} == -* ]] ; then
		COMPREPLY=( $(compgen -W "${mopts}" -- ${cur}) )
		return 0
	fi

	COMPREPLY=( $(compgen -W "${mopts} ${mmopts}" -- ${cur}) )
	return 0

}
complete -F _sm sm
