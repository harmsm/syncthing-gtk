#!/usr/bin/env python2
"""
Syncthing-GTK - Configuration

Configuration object implementation; Uses JSON.
Config file is by default in ~/.config/syncthing-gtk/config.json
or other ~/.config equivalent
"""

from __future__ import unicode_literals
from syncthing_gtk.tools import *
from datetime import datetime
import dateutil.parser
import os, sys, json


LONG_AGO = datetime.fromtimestamp(1)

class _Configuration(object):
	"""
	Configuration object implementation.
	Use like dict to save / access values
	"""
	
	# Dict with keys that are reqiured in configuration file
	# and default values for thoose keys.
	# Format: key : (type, default)
	REQUIRED_KEYS = {
		"autostart_daemon"			: (int, 2),	# 0 - wait for daemon, 1 - autostart, 2 - ask
		"autokill_daemon"			: (int, 2),	# 0 - never kill, 1 - always kill, 2 - ask
		"syncthing_binary"			: (str, "/usr/bin/syncthing"),
		"minimize_on_start"			: (bool, False),
		"use_inotify"				: (list, []),
		"use_old_header"			: (bool, False),
		"icons_in_menu"				: (bool, True),
		"notification_for_update"	: (bool, True),
		"notification_for_folder"	: (bool, False),
		"notification_for_error"	: (bool, True),
		"st_autoupdate"				: (bool, False),
		"last_updatecheck"			: (datetime, LONG_AGO),
		"window_position"			: (tuple, None),
	}
	
	# Overrides some default values on Windows
	WINDOWS_OVERRIDE = {
		"syncthing_binary"			: (str, "C:\\Program Files\\Syncthing\\syncthing.exe"),
		"autokill_daemon"			: (int, 1),
		"use_old_header"			: (bool, True),
		"st_autoupdate"				: (bool, True),
	}
	
	def __init__(self):
		try:
			self.load()
		except Exception, e:
			print >>sys.stderr, "Warning: Failed to load configuration; Creating new one"
			print >>sys.stderr, "  exception was:", e
			self.create()
		
		# Convert objects serialized as string back to object
		self.convert_values()
		# Check if everything is in place, add default value
		# where value is missing
		if self.check_values():
			# check_values returns True if any default value is added
			print "SAVE"
			self.save()
	
	def load(self):
		# Check & create directory
		if not os.path.exists(self.get_config_dir()):
			try:
				os.makedirs(self.get_config_dir())
			except Exception, e:
				print >>sys.stderr, "Fatal: Cannot create configuration directory"
				print >>sys.stderr, e
				sys.exit(1)
		# Load json
		self.values = json.loads(file(self.get_config_file(), "r").read())
	
	def get_config_dir(self):
		return os.path.join(get_config_dir(), "syncthing-gtk")
	
	def get_config_file(self):
		return os.path.join(self.get_config_dir(), "config.json")
	
	def create(self):
		""" Creates new, empty configuration """
		self.values = {}
		self.check_values()
		self.save()
	
	def check_values(self):
		"""
		Check if all required values are in place and fill by default
		whatever is missing.
		
		Returns True if anything gets changed.
		"""
		needs_to_save = False
		for key in Configuration.REQUIRED_KEYS:
			tp, default = Configuration.REQUIRED_KEYS[key]
			if not self.check_type(key, tp):
				if IS_WINDOWS and key in Configuration.WINDOWS_OVERRIDE:
					tp, default = Configuration.WINDOWS_OVERRIDE[key]
				self.values[key] = default
				needs_to_save = True
		return needs_to_save
	
	def convert_values(self):
		"""
		Converts all objects serialized as string back to object
		"""
		for key in Configuration.REQUIRED_KEYS:
			if key in self.values:
				tp, trash = Configuration.REQUIRED_KEYS[key]
				try:
					if tp == datetime and type(self.values[key]) in (str, unicode):
						# Parse datetime
						self.values[key] = dateutil.parser.parse(self.values[key])
					elif tp == tuple and type(self.values[key]) == list:
						# Convert list to tuple
						self.values[key] = tuple(self.values[key])
					elif tp == bool and type(self.values[key]) in (int, long):
						# Convert bools
						self.values[key] = bool(self.values[key])
				except Exception, e:
					print >>sys.stderr, "Warning: Failed to parse configuration value '%s'. Using default." % (key,)
					print >>sys.stderr, e
					# Value will be re-created by check_values method
					del self.values[key]
	
	def check_type(self, key, tp):
		"""
		Returns True if value is set and type match.
		Auto-converts objects serialized as string back to objects
		"""
		if not key in self.values:
			return False
		# Handle special cases
		if type(self.values[key]) in (str, unicode) and tp in (str, unicode):
			return True
		# Return value
		return type(self.values[key]) == tp
	
	def save(self):
		""" Saves configuration file """
		file(self.get_config_file(), "w").write(json.dumps(
			self.values, sort_keys=True, indent=4,
			separators=(',', ': '), default=serializer
			))
	
	def __iter__(self):
		for k in self.values:
			yield k
	
	def get(self, key):
		return self.values[key]
	
	def set(self, key, value):
		self.values[key] = value
		self.save()
	
	__getitem__ = get
	__setitem__ = set
	
	def __contains__(self, key):
		""" Returns true if there is such value """
		return key in self.values

def serializer(obj):
	""" Handles serialization where json can't do it by itself """
	if hasattr(obj, "isoformat"):
		# datetime object
		return obj.isoformat()
	raise TypeError("Can't serialize object of type %s" % (type(obj),))

Configuration = _Configuration
if IS_WINDOWS:
	from syncthing_gtk.windows import WinConfiguration
	Configuration = WinConfiguration()
