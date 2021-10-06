'''
Copyright 2021 Flexera Software LLC
See LICENSE.TXT for full license text
SPDX-License-Identifier: MIT

Author : sgeary  
Created On : Wed Oct 06 2021
File : report_data.py
'''
import logging
import CodeInsight_RESTAPIs.project.get_child_projects
import CodeInsight_RESTAPIs.project.get_inventory_summary
import CodeInsight_RESTAPIs.license.license_lookup

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------#
def gather_data_for_report(baseURL, projectID, authToken, reportName, reportOptions):
    logger.info("Entering gather_data_for_report")

    # Parse report options
    includeChildProjects = reportOptions["includeChildProjects"]  # True/False

    projectList = [] # List to hold parent/child details for report
    inventoryData = {}  # Create a dictionary containing the inventory data using inventoryID as keys
    projectData = {} # Create a dictionary containing the project level summary data using projectID as keys
    licenseDetails = {} # Dictionary to store license details to avoid multiple lookups for same id

    # Get the list of parent/child projects start at the base project
    projectHierarchy = CodeInsight_RESTAPIs.project.get_child_projects.get_child_projects_recursively(baseURL, projectID, authToken)

    # Create a list of project data sorted by the project name at each level for report display  
    # Add details for the parent node
    nodeDetails = {}
    nodeDetails["parent"] = "#"  # The root node
    nodeDetails["projectName"] = projectHierarchy["name"]
    nodeDetails["projectID"] = projectHierarchy["id"]
    nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectHierarchy["id"]) + "&tab=projectInventory"

    projectList.append(nodeDetails)

    if includeChildProjects:
        projectList = create_project_hierarchy(projectHierarchy, projectHierarchy["id"], projectList, baseURL)
    else:
        logger.debug("Child hierarchy disabled")

    projectInventoryCount = {}

    #  Gather the details for each project and summerize the data
    for project in projectList:

        projectID = project["projectID"]
        projectName = project["projectName"]
        projectLink = project["projectLink"]

        projectInventorySummary = CodeInsight_RESTAPIs.project.get_inventory_summary.get_project_inventory_without_vulns_summary(baseURL, projectID, authToken)

        if not projectInventorySummary:
            logger.warning("    Project contains no inventory items")
            print("Project contains no inventory items.")

        # Create empty dictionary for project level data for this project
        projectData[projectName] = {}

        currentItem=0
        projectInventoryCount[projectName] = len(projectInventorySummary)

        for inventoryItem in projectInventorySummary:
            currentItem +=1

            inventoryID = inventoryItem["id"]
            inventoryItemName = inventoryItem["name"]

            logger.debug("Processing inventory items %s of %s" %(currentItem, len(projectInventorySummary)))
            logger.debug("    %s - %s" %(inventoryID, inventoryItemName))
            
            componentName = inventoryItem["componentName"]
            componentID = inventoryItem["componentId"]
            componentVersionName = inventoryItem["componentVersionName"]
            selectedLicenseID = inventoryItem["selectedLicenseId"]
            selectedLicenseName = inventoryItem["selectedLicenseSPDXIdentifier"]


            if selectedLicenseID in licenseDetails.keys():
                selectedLicenseName = licenseDetails[selectedLicenseID]["selectedLicenseName"]
                selectedLicenseUrl = licenseDetails[selectedLicenseID]["selectedLicenseUrl"]
            else:
                if selectedLicenseID != "N/A":  
                    logger.debug("Fetching license details for %s with ID %s" %(selectedLicenseName, selectedLicenseID ))
                    licenseInformation = CodeInsight_RESTAPIs.license.license_lookup.get_license_details(baseURL, selectedLicenseID, authToken)
                    licenseURL = licenseInformation["url"]
                    spdxIdentifier = licenseInformation["spdxIdentifier"]
                    licensePriority = licenseInformation["priority"]

                    if spdxIdentifier != "":
                        licenseName = spdxIdentifier
                    else:
                        licenseName = licenseInformation["shortName"]

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

            
            componentUrl = inventoryItem["url"]
            inventoryLink = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(projectID) + "&tab=projectInventory&pinv=" + str(inventoryID)

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
                "projectLink" : projectLink
            }

            projectData[projectName]["projectLink"] = projectLink



    # Build up the data to return for the
    reportData = {}
    reportData["reportName"] = reportName
    reportData["projectHierarchy"] = projectHierarchy
    reportData["projectName"] = projectHierarchy["name"]
    reportData["projectID"] = projectHierarchy["id"]
    reportData["inventoryData"] = inventoryData
    reportData["projectList"] =projectList

    return reportData


#----------------------------------------------#
def create_project_hierarchy(project, parentID, projectList, baseURL):
    logger.debug("Entering create_project_hierarchy")

    # Are there more child projects for this project?
    if len(project["childProject"]):

        # Sort by project name of child projects
        for childProject in sorted(project["childProject"], key = lambda i: i['name'] ) :

            nodeDetails = {}
            nodeDetails["projectID"] = childProject["id"]
            nodeDetails["parent"] = parentID
            nodeDetails["projectName"] = childProject["name"]
            nodeDetails["projectLink"] = baseURL + "/codeinsight/FNCI#myprojectdetails/?id=" + str(childProject["id"]) + "&tab=projectInventory"

            projectList.append( nodeDetails )

            create_project_hierarchy(childProject, childProject["id"], projectList, baseURL)

    return projectList