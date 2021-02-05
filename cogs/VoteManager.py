"""
	Create and handle polls and votes

	Access database with questions and results stored
	This would support up to a certain number of options
		Tables
			polls
				poll id - int
				message id - int
				created by - int (user id)
				created at - date
				question - string
				expiration - date
				number of options - int
			votes
				poll id - int
				voter id - int (user id)
				voted at - date
				option selected - int
				unique - poll id, voter id

	Poll
		Create text poll
			Assemble question, including text based options if necessary
		Add options as reactions
		Capture any reactions added to that message id
			Allow "secret" votes by immediately removing the user's vote
		Dump results
"""
