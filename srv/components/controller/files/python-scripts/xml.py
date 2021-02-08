import logging
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

log_dir = '/var/log/seagate/provisioner/'
xml_cmd = "/usr/bin/xmllint"
xml_doc = log_dir + "tmp.xml"

tree = ET.parse(xml_doc)
root = tree.getroot()


def validate_xml():
	logger.debug(f"validate_xml():{xml_doc}")
	if subprocess.check_call([xml_cmd, '--noout', xml_doc]):
		logger.error("Invalid XML input")
		sys.exit(1)
	logger.debug(f"validate_xml():done - {xml_doc}")


def cli_status_get():
	logger.debug(f"cli_status_get(): {xml_doc}")
	response_type_obj_list = root.findall(".//PROPERTY[@name='response-type']")
	node_cnt = len(response_type_obj_list)
	status = response_type_obj_list[node_cnt - 1].text
	response_obj_list = root.findall(".//PROPERTY[@name='response']")
	status_msg = response_obj_list[node_cnt - 1].text
	if status != "Success":
		logger.error("Command failed on the controller with the following error:")
		logger.error(f"{status_msg}")
		sys.exit(1)
	logger.debug("cli_status_get(): Command run successfully")


def parse_xml(base_type, elements):
	logger.debug(f"parse_xml: parsing {xml_doc}")
	logger.debug(f"parse_xml(): basetype={base_type}, _elements=('{elements}')")
	_cnt = len(root.findall(f"./OBJECT[@basetype='{base_type}']"))
	for i in range(1, _cnt + 1):
		logger.debug(f"parse_xml(): cnt={_cnt}, loop:{i}")
		values = []
		for e in elements:
			av = root.findall("./OBJECT[@basetype='{base_type}'][{i}]/PROPERTY[@name='{e}'")[0].text
			logger.debug(f"parse_xml(): loop:{i}, element={e}, av={av}")
			if av == "":
				logger.debug(f"parse_xml(): element={e} has no value")
				av = "N/A"
			values.append(av)
		logger.debug(f"parse_xml(): end of loop for elements, values={values}")
		logger.debug(f"{values}")
	logger.debug(f"parse_xml(): done")


def ctrl_activity_get(_xml_doc):
	prg_tree = ET.parse(_xml_doc)
	prg_root = prg_tree.getroot()

	ctrl_activity_a = None
	ctrl_activity_b = None

	if not os.path.isfile(_xml_doc):
		logger.warning(f"WARNING: could not find the file {_xml_doc}, not parsing the progress file.")
		sys.exit(1)

	logger.debug(f"DEBUG: ctrl_activity_get: parsing {_xml_doc}")
	logger.debug(f"DEBUG: ctrl_activity_get() contents of progress xml")

	# TODO: append _xml_doc content to logfile

	_activity_list = prg_root.findall(".//RESPONSE[@CONTROLLER='A']")
	_activity = None

	if len(_activity_list) == 1:
		_activity = _activity_list[0].attrib['ACTIVITY']

	ctrl_activity_a = _activity
	logger.debug(f"DEBUG: ctrl_activity_get(): ctrl_activity_a={ctrl_activity_a}")

	_activity_list = prg_root.findall(".//RESPONSE[@CONTROLLER='B']")
	_activity = None
	if len(_activity_list) == 1:
		_activity = _activity_list[0].attrib['ACTIVITY']

	ctrl_activity_b = _activity
	logger.debug(f"DEBUG: ctrl_activity_get(): ctrl_activity_b={ctrl_activity_b}")

	os.remove(_xml_doc)
