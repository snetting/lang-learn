#!/bin/bash
# Thrown together to assist with learning a language
# - please don't judge me ;)
# language data file is colon separated values intended as simple
# word:word translation pairs.  The script will select random pairs plus
# randomly swap the translation direction.

# Calculate number of lines, read file into array
FSIZE=$(wc -l langlearn.dat | sed '/^$/d' | awk '{ print $1 }')
IFS=$'\r\n' GLOBIGNORE='*' command eval  'DBARR=($(cat langlearn.dat | sed '/^$/d'))'
echo -e "\ndb size: $FSIZE"
echo "ctrl-c to exit"

# Set some vars
POINTS=0  # correct answers
TOTAL=0   # total iterations


# fuction to randomise question
function juggle {
	RLINE=$(( RANDOM % $FSIZE ))
	RDATA=${DBARR[$RLINE]}
        RSWAP=$(( RANDOM % 2))
        VARA=$(echo $RDATA | cut -d":" -f1 | tr '[:upper:]' '[:lower:]')
        VARB=$(echo $RDATA | cut -d":" -f2 | tr '[:upper:]' '[:lower:]')
        if [ $RSWAP -eq 1 ]; then
                VARC=$VARA; VARA=$VARB; VARB=$VARC
        fi

}

# function on quit;  print results
function control_c {
	echo -e "\n\n---"
	echo "Final Score: $POINTS / $TOTAL"
	echo -e "Goodbye!\n---\n"
	exit 0
}

trap control_c SIGINT

# loop and question
# on incorrect answer ask user to type both words (memory aid, not checked)
while true; do
	juggle
	echo -en "\n---\nTranslate $VARA : ";
	read RAWINPUT
	INPUT=$(echo $RAWINPUT | tr '[:upper:]' '[:lower:]')
	#echo "read: $INPUT, is $INPUT = $VARB ?"
	if [ "$INPUT" = "$VARB" ]; then
		echo "Correct!"
		POINTS=$(expr $POINTS + 1)
	else
		echo "Wrong - correct answer is $VARB"
		echo -n "Type: $VARA is $VARB: "
		read INPUT
	fi
	TOTAL=$(expr $TOTAL + 1)
	echo "Score: $POINTS / $TOTAL"
done

