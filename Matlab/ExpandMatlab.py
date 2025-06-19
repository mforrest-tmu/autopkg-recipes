#!/usr/local/autopkg/python
#
# Copyright 2025 Matt Forrest <mforrest@torontomu.ca>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""See docstring for ExpandMatlab class"""


import os.path
from glob import glob

from autopkglib import ProcessorError

from autopkglib.DmgMounter import DmgMounter


from autopkglib import Copier
#import zipfile # messes up permissions
import subprocess # use external unzip to keep permissions
import re


__all__ = ["ExpandMatlab"]


class ExpandMatlab(DmgMounter):
	"""Converts the Matlab installer script into .zip and expands it into the provided directory

	"""

	input_variables = {
		"ml_dmg": {
			"description": "dmg containing the Matlab installer",
			"default": "%RECIPE_CACHE_DIR%/R2025a.dmg",
			"required": True,
		},
		"ml_dir": {
			"description": (
				"directory to expand the installer into"
			),
			"default": "%RECIPE_CACHE_DIR%/Scripts/ml-installer",
			"required": True,
		},
		"ml_inst": {
			"description": (
				"glob for the Matlab installer name"
				'default: *InstallForMacOS*.app/Contents/MacOS/InstallForMacOS*'
			),
			"default": "*InstallForMacOS*.app/Contents/MacOS/InstallForMacOS*",
			"required": False,
		},
	}
	output_variables = {
#		 "found_filename": {"description": "Full path of found filename"},
#		 "dmg_found_filename": {"description": "DMG-relative path of found filename"},
#		 "found_basename": {"description": "Basename of found filename"},
		"version": {"description": "full version from VersionInfo.xml"},
		"update": {"description": "update version from VersionInfo.xml"},

	}

	description = __doc__

	def globfind(self, pattern):
		"""If multiple files are found the last alphanumerically sorted found
		file is returned"""

		glob_matches = glob(pattern, recursive=True)

		if len(glob_matches) < 1:
			raise ProcessorError("No matching filename found")

		glob_matches.sort()

		return glob_matches[-1]

	def main(self):
		ml_dmg = self.globfind(self.env.get("ml_dmg"))
		ml_dir = self.env.get("ml_dir")
		ml_inst = self.env.get("ml_inst")
		ml_cache = os.path.join( self.env.get("RECIPE_CACHE_DIR"), "ml_cache")
		orig_version = self.env.get("version")
		version = ""



		source_path = os.path.join(ml_dmg, ml_inst)

		# Check if we're trying to copy something inside a dmg.
		(dmg_path, dmg, dmg_source_path) = self.parsePathForDMG(source_path)
		try:
			if dmg:
				# Mount dmg and copy path inside.
				mount_point = self.mount(dmg_path)
				source_path = os.path.join(mount_point, dmg_source_path)
			# process path with globbing
			match = self.globfind(source_path)
			self.output(
				f"Found file match: '{match}' from globbed '{source_path}'"
			)

			if dmg and match.startswith(mount_point):
				# create dir if needed
				if not os.path.exists(ml_dir):
					os.makedirs(ml_dir,exist_ok=True)

				# cp installer into cache
				self.output(f"Copying data from dmg", verbose_level=1)
				Copier.copy( self, match, ml_cache, overwrite=True )
				
				# find num lines to strip
				# strip lines
				self.output(f"Extrating data from installer", verbose_level=1)
				str = "tail -n +"
				delim_tail = str.encode()
				
				str = "exit 0"
				delim_exit = str.encode()
				
				ml_zip = ml_cache + ".zip"
				line_tail = line_exit = found_zip = cur_pos = 0
				with open(ml_cache, 'rb') as infile, \
					open(ml_zip, 'wb') as outfile:
					line_num=0
					while True :
						cur_pos = infile.tell()
						line_content = infile.readline()
						line_num = line_num + 1
						
						if not line_content : # EOF
							break
							
						if found_zip == 0 and delim_tail in line_content:
							match = re.search(r'tail -n \+(\d+)', line_content.decode())
							if match:
								line_tail = int(match.group(1)) -1
#							print(f"tail:'{line_tail}' n:'{line_num}' line:'{line_content}'")
#							next(infile, None)

						elif found_zip == 0 and delim_exit in line_content:
							line_exit = line_num
#							print(f"exit:'{line_num}' line:'{line_content}'")
							found_zip = line_num + 1
							cur_pos += len(line_content)
							break;
#							next(infile, None)

					if found_zip :
						outfile.write(infile.read())
						self.output(f"wrote binary .zip", verbose_level=1)
					
					
					
					
 
#				# unzip into dir - keep permissions
				self.output(f"Expanding .zip", verbose_level=1)
				p=subprocess.run(['unzip', ml_zip, '-d', ml_dir], capture_output=True, text=True)
				if p.returncode != 0 :
					self.output( f"Error with unzip:")								
				if p.stdout:
					self.output( f"unzip output: {p.stdout}", verbose_level=4)				
				if p.stderr:
					self.output( f"unzip errors: {p.stderr}", verbose_level=4)				

				p=subprocess.run(['chmod', '-R', 'u+rw', ml_dir], capture_output=True, text=True)
				if p.returncode != 0 :
					self.output( f"Error with chmod:")								
				if p.stdout:
					self.output( f"chmod output: {p.stdout}", verbose_level=4)				
				if p.stderr:
					self.output( f"chmod errors: {p.stderr}", verbose_level=4)				



#				# unzip into dir
#				try:
#					with zipfile.ZipFile(ml_zip, 'r') as zip_ref:
#						print(f"Extracting '{ml_zip}' to '{ml_dir}'...")
#						zip_ref.extractall(ml_dir)
#						print("Extraction complete!")
#						return True
#				except zipfile.BadZipFile:
#					print(f"Error: The zip file is corrupted or invalid.")
#					return False
#				except Exception as e:
#					print(f"An unexpected error occurred during extraction: {e}")
#					return False
# 

				self.output(f"Reading VersionInfo", verbose_level=1)
				with open(os.path.join(ml_dir, "VersionInfo.xml")) as version_file :
					for line in version_file :
						match = re.search(r'<version>([\d\.]+)</version>', line)
						if match :
							version = "v" + match.group(1)
							if orig_version :
								version = version + "-" + orig_version
						
							self.env["version"] = version
							self.output(
								f"Found version: '{match.group(1)}' using version: '{version}'",
								verbose_level=1
							)
						match = re.search(r'<description>Update ([\d]+)</description>', line)
						if match :
							self.env["update"] = ".u" + match.group(1)
							self.output(
								f"Found update: '{match.group(1)}'",
								verbose_level=1
							)


				

		finally:
			if dmg:
				self.unmount(dmg_path)


if __name__ == "__main__":
	PROCESSOR = ExpandMatlab()
	PROCESSOR.execute_shell()
