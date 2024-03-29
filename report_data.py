'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Oct 06 2021
File : report_data.py
'''
import logging
from collections import OrderedDict

import common.application_details
import common.project_heirarchy
import common.api.project.get_inventory_summary
import common.api.project.get_project_information
import common.api.license.license_lookup

import purl

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)  # Disable logging for requests module


#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportData):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    reportOptions = reportData["reportOptions"]
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False
    includeVulnerabilities = reportOptions["includeVulnerabilities"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    projectData = {} # Create a dictionary containing the project level summary data using projectID as keys
    licenseDetails = {} # Dictionary to store license details to avoid multiple lookups for same id
    applicationDetails = {} # Dictionary to allow a project to be mapped to an application name/version

    # applicationDetails = common.application_details.determine_application_details(projectID, baseURL, authToken)
    projectList = common.project_heirarchy.create_project_heirarchy(baseURL, authToken, projectID, includeChildProjects)
    topLevelProjectName = projectList[0]["projectName"]

    # Get the list of parent/child projects start at the base project
    projectHierarchy = common.api.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)

    projectInventoryCount = {}

    #  Gather the details for each project and summerize the data
    for project in projectList:

        projectID = project["projectID"]
        projectName = project["projectName"]
        projectLink = project["projectLink"]

        applicationDetails[projectName] = determine_application_details(baseURL, projectName, projectID, authToken)
        applicationNameVersion = applicationDetails[projectName]["applicationNameVersion"]
           
        # Add the applicationNameVersion to the project hierarchy
        project["applicationNameVersion"] = applicationNameVersion
             
        # Include vulnerability data?
        if includeVulnerabilities:
            # Just default to v3 summary data
            projectInventorySummary = common.api.project.get_inventory_summary.get_project_inventory_with_v3_summary(baseURL, projectID, authToken)
        else:
            projectInventorySummary = common.api.project.get_inventory_summary.get_project_inventory_without_vulns_summary(baseURL, projectID, authToken)

        
        if not projectInventorySummary:
            logger.warning("    Project contains no inventory items")
            print("Project contains no inventory items.")

        # Create empty dictionary for project level data for this project
        projectData[projectName] = {}

        currentItem=0
        projectInventoryCount[projectName] = len(projectInventorySummary)

        for inventoryItem in projectInventorySummary:

            inventoryType = inventoryItem["type"]
            
            # This is not a component for move to the next item
            if inventoryType != "Component":
                continue

            currentItem +=1

            inventoryID = inventoryItem["id"]
            inventoryItemName = inventoryItem["name"]

            logger.debug("Processing inventory items %s of %s" %(currentItem, len(projectInventorySummary)))
            logger.debug("    Project:  %s   Inventory Name: %s  Inventory ID: %s" %(projectName, inventoryItemName, inventoryID))
            
            componentName = inventoryItem["componentName"]
            componentVersionName = inventoryItem["componentVersionName"]
            selectedLicenseID = inventoryItem["selectedLicenseId"]
            selectedLicenseName = inventoryItem["selectedLicenseSPDXIdentifier"]

            if reportData["releaseVersion"] >= "2024R1":
                purlString = inventoryItem["purl"]
            else:
                # Attempt to generate a purl string for the component
                try:
                    purlString = purl.get_purl_string(inventoryItem, baseURL, authToken)
                except:
                    logger.warning("Unable to create purl string for inventory item %s." %inventoryItemName)
                    purlString = ""


            if selectedLicenseID in licenseDetails.keys():
                selectedLicenseName = licenseDetails[selectedLicenseID]["selectedLicenseName"]
                selectedLicenseUrl = licenseDetails[selectedLicenseID]["selectedLicenseUrl"]
            else:
                if selectedLicenseID != "N/A":  
                    logger.debug("        Fetching license details for %s with ID %s" %(selectedLicenseName, selectedLicenseID ))
                    licenseInformation = common.api.license.license_lookup.get_license_details(baseURL, selectedLicenseID, authToken)
                    licenseURL = licenseInformation["url"]
                    spdxIdentifier = licenseInformation["spdxIdentifier"]
                    licensePriority = licenseInformation["priority"]

                    if spdxIdentifier != "" and spdxIdentifier != "N/A":
                        licenseName = spdxIdentifier
                    else:
                        licenseName = licenseInformation["shortName"]

                    # There is not specific selected licesne just let it be blank
                    if licenseName == "I don't know":
                        licenseName = ""

                    licenseDetails[selectedLicenseID] = {}
                    licenseDetails[selectedLicenseID]["selectedLicenseName"] = licenseName
                    licenseDetails[selectedLicenseID]["selectedLicenseUrl"] = licenseURL
                    licenseDetails[selectedLicenseID]["selectedLicensePriority"] = licensePriority

                    selectedLicenseName = licenseName
                    selectedLicenseUrl = licenseURL

                else:
                    # Typically a WIP item
                    selectedLicenseName = ""
                    selectedLicenseUrl = ""     

            # If there is no specific version just leave it blank
            if componentVersionName == "N/A":
                componentVersionName = ""

            # If there is no license URL set it to blank
            if selectedLicenseUrl is None:
                selectedLicenseUrl = ""

            componentUrl = inventoryItem["url"]
            inventoryLink = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectID) + "&tab=projectInventory&pinv=" + str(inventoryID)

            # Determine if there are any vulnerabilities
            try:
                vulnerabilities = inventoryItem["vulnerabilitySummary"][0]["CvssV3"]
                
                if sum(vulnerabilities.values()):
                    hasVulnerabilities=True
                else:
                    hasVulnerabilities=False

            except:
                logger.info("        No vulnerabilies for %s - %s" %(componentName, componentVersionName))
                hasVulnerabilities=False


            # Store the data for the inventory item for reporting
            inventoryData[inventoryID] = {
                "projectName" : projectName,
                "inventoryItemName" : inventoryItemName,
                "componentName" : componentName,
                "componentVersionName" : componentVersionName,
                "selectedLicenseName" : selectedLicenseName,
                "componentUrl" : componentUrl,
                "selectedLicenseUrl" : selectedLicenseUrl,
                "inventoryLink" : inventoryLink,
                "projectLink" : projectLink,
                "hasVulnerabilities" : hasVulnerabilities,
                "applicationNameVersion" : applicationNameVersion,
                "purlString" : purlString
            }

            projectData[projectName]["projectLink"] = projectLink

    # Sort the inventory data by Component Name / Component Version / Selected License Name
    sortedInventoryData = OrderedDict(sorted(inventoryData.items(), key=lambda x: (x[1]['componentName'],  x[1]['componentVersionName'], x[1]['selectedLicenseName'])  ) )

    # Build up the data to return for the
    reportData["projectHierarchy"] = projectHierarchy
    reportData["topLevelProjectName"] = topLevelProjectName
    reportData["inventoryData"] = sortedInventoryData
    reportData["projectList"] =projectList
    reportData["reportOptions"] =reportOptions
    reportData["projectInventoryCount"] = projectInventoryCount
    reportData["applicationDetails"] = applicationDetails

    return reportData


#----------------------------------------------#
def create_project_hierarchy(project, parentID, projectList, baseURL):
    logger.debug("Entering create_project_hierarchy.")
    logger.debug("    Project Details: %s" %project)

    # Are there more child projects for this project?
    if len(project["childProject"]):

        # Sort by project name of child projects
        for childProject in sorted(project["childProject"], key = lambda i: i['name'] ) :

            uniqueProjectID = str(parentID) + "-" + str(childProject["id"])
            nodeDetails = {}
            nodeDetails["projectID"] = childProject["id"]
            nodeDetails["parent"] = parentID
            nodeDetails["uniqueID"] = uniqueProjectID
            nodeDetails["projectName"] = childProject["name"]
            nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(childProject["id"]) + "&tab=projectInventory"

            projectList.append( nodeDetails )

            create_project_hierarchy(childProject, uniqueProjectID, projectList, baseURL)

    return projectList

#----------------------------------------------#
def determine_application_details(baseURL, projectName, projectID, authToken):
    logger.debug("Entering determine_application_details.")
    # Create a application name for the report if the custom fields are populated
    # Default values
    applicationName = projectName
    applicationVersion = ""
    applicationPublisher = ""
    applicationDetailsString = ""

    projectInformation = common.api.project.get_project_information.get_project_information_summary(baseURL, projectID, authToken)

    # Project level custom fields added in 2022R1
    if "customFields" in projectInformation:
        customFields = projectInformation["customFields"]

        # See if the custom project fields were propulated for this project
        for customField in customFields:

            # Is there the reqired custom field available?
            if customField["fieldLabel"] == "Application Name":
                if customField["value"]:
                    applicationName = customField["value"]

            # Is the custom version field available?
            if customField["fieldLabel"] == "Application Version":
                if customField["value"]:
                    applicationVersion = customField["value"]     

            # Is the custom Publisher field available?
            if customField["fieldLabel"] == "Application Publisher":
                if customField["value"]:
                    applicationPublisher = customField["value"]    



    # Join the custom values to create the application name for the report artifacts
    if applicationName != projectName:
        if applicationVersion != "":
            applicationNameVersion = applicationName + " - " + applicationVersion
        else:
            applicationNameVersion = applicationName
    else:
        applicationNameVersion = projectName

    if applicationPublisher != "":
        applicationDetailsString += "Publisher: " + applicationPublisher + " | "

    # This will either be the project name or the supplied application name
    applicationDetailsString += "Application: " + applicationName + " | "

    if applicationVersion != "":
        applicationDetailsString += "Version: " + applicationVersion
    else:
        # Rip off the  | from the end of the string if the version was not there
        applicationDetailsString = applicationDetailsString[:-3]

    applicationDetails = {}
    applicationDetails["applicationName"] = applicationName
    applicationDetails["applicationVersion"] = applicationVersion
    applicationDetails["applicationPublisher"] = applicationPublisher
    applicationDetails["applicationNameVersion"] = applicationNameVersion
    applicationDetails["applicationDetailsString"] = applicationDetailsString

    logger.info("    applicationDetails: %s" %applicationDetails)

    return applicationDetails