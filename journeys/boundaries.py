"""The Boundaries Journey"""
from flask import jsonify, request
from absl import logging
import pygal

def get_quiz_infographic(request):

	# Get the inputs.
	message_body = request.json

	# Get the list of results.
	results = message_body['results']

	# Count the "Yes"s and the "No"s.
	results = [r.lower() for r in results]
	results = ['yes' if 'yes' in r else 'no' for r in results]
	num_yes = results.count('yes')
	num_no = results.count('no')

	# Make a plot.
	pie_chart = pygal.Pie(half_pie=True)
	pie_chart.title = 'Browser usage in February 2012 (in %)'
	pie_chart.add('Yes', num_yes)
	pie_chart.add('No', num_no)
	pie_chart.add('Other', len(results) - (num_yes + num_no))
	pie_chart.render_in_browser()

	return jsonify(
		num_yes=num_yes,
		num_no=num_no)