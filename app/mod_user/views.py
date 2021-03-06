from random import randint
from flask import Blueprint, g, current_app, render_template, flash, redirect, request, url_for, jsonify, session
from flask.ext.login import current_user, login_required, login_user
from flask.ext.babel import gettext as _

from app.utils import url_for_school
from app.mod_school import get_school_context
from .forms import UserSettingsForm, PasswordForm, UserAddForm
from .models import User
from .services import can_edit, can_edit_user


# Blueprint definition
users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/<id>', methods=['GET'])
def detail(id):
	""" Show a single userproposal, redirecting to the appropriate school if necessary """
	u = User.objects.get_or_404(id=id)
	c = get_school_context(u)
	if not g.school==c:
		flash(_("You've been redirected to the school the user is following."))
		return redirect(url_for_school('users.detail', school=c, id=u.id), code=301)
	return render_template('user/detail.html',
		title = u.display_name,
		user = u)



@users.route('/edit/<id>', methods=['GET', 'POST'])
@users.route('/edit', methods=['GET', 'POST'])
@can_edit
@login_required
def edit(id=None):
	""" Edit a user """
	if id:
		u = User.objects.get_or_404(id=id)
	else:
		u = current_user._get_current_object()
	form = UserSettingsForm(request.form, u)
	# submit
	if form.validate_on_submit():
		form.populate_obj(u)
		u.save()
		flash(_("The settings have been saved"), 'success')
	return render_template('user/settings.html',
		title=_('Edit settings'),
		user = u,
		form=form)


@users.route('/password', methods=['GET', 'POST'])
@login_required
def password():
	user = current_user._get_current_object()
	form = PasswordForm(next=request.args.get('next'))
	if form.validate_on_submit():
		user.set_password(form.new_password.data)
		user.save()
		flash(_('Password updated.'), 'success')
		return redirect(url_for('users.edit'))
	return render_template('user/password.html',
		user=user,
		form=form)


@users.route('/create', methods=['GET', 'POST'])
def create():
	""" Register a new user """
	# create the form
	form = UserAddForm(request.form, schools=[g.school,], next=request.args.get('next'))
	# submit
	if form.validate_on_submit():
		# This is a honeypot and we act like it was successful
		if form.captcha.data:
			flash(_("Welcome to the website!"), 'success')
			return redirect(form.next.data or url_for('schools.home'))
		u = User(password=form.new_password.data)
		form.populate_obj(u)
		u.save()
		login_user(u)
		flash(_("Welcome %(user)s!", user=u.display_name), 'success')
		return redirect(form.next.data or url_for_school('schools.home', user_school=True))
	# Our simple custom captcha implementation
	gotcha = 'which letter in this sentence is uppercase?'
	idx = randint(0, len(gotcha)-1)
	form.gotcha.label = gotcha[:idx].lower() + gotcha[idx:].capitalize()
	session['gotcha'] = gotcha[idx]
	return render_template('user/create.html',
		title=_('Create an account'),
		form=form)
