'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Oct 06 2021
File : report_artifacts.py
'''
import logging

import report_artifacts_html
import report_artifacts_xlsx

logger = logging.getLogger(__name__)

#--------------------------------------------------------------------------------#
def create_report_artifacts(reportData):
    logger.info("Entering create_report_artifacts")

    reportName = reportData["reportName"]
    projectNameForFile  = reportData["projectNameForFile"] 
    projectID = reportData["projectID"] 
    fileNameTimeStamp = reportData["fileNameTimeStamp"] 
    projectList = reportData["projectList"]

    # Are there child projects involved?  If so have the file name reflect this fact
    if len(projectList)==1:
        reportNameBase = projectNameForFile + "-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp
    else:
        reportNameBase = projectNameForFile + "-with-children-" + str(projectID) + "-" + reportName.replace(" ", "_") + "-" + fileNameTimeStamp

    # Dict to hold the complete list of reports
    reports = {}

    htmlFile = report_artifacts_html.generate_html_report(reportData, reportNameBase)
    xlsxFile = report_artifacts_xlsx.generate_xlsx_report(reportData, reportNameBase)
    reports["viewable"] = htmlFile
    reports["allFormats"] = [htmlFile, xlsxFile]

    logger.info("Exiting create_report_artifacts")
    
    return reports 

