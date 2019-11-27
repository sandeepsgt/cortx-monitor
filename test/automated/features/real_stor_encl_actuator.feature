Feature: Test Enclosure Actuator Capabilities
    Send Enclosure request message to SSPL and
    verify the response messages contain the correct information.

Scenario: Send SSPL an enclosure actuator message requesting fan_module data
    Given that SSPL is running
    When I send in the enclosure actuator message to request the current "ENCL:enclosure:fru:fan" data with instance id "4"
    Then I get the fan module JSON response message

Scenario: Send SSPL an enclosure actuator message requesting fan_module data
    Given that SSPL is running
    When I send in the enclosure actuator message to request the current "ENCL:enclosure:fru:fan" data with instance id "*"
    Then I get the fan module JSON response message

Scenario: Send SSPL-LL a disk actuator message requesting single-instance disk data
	Given that SSPL is running
    When I send in the enclosure actuator message to request the current "ENCL:enclosure:fru:disk" data with instance id "65"
	Then I get the disk actuator JSON response message for disk instance "65"

Scenario: Send SSPL-LL a disk actuator message requesting multi-instance disk data
	Given that SSPL is running
    When I send in the enclosure actuator message to request the current "ENCL:enclosure:fru:disk" data with instance id "*"
	Then I get the disk actuator JSON response message for disk instance "*"

Scenario: Send SSPL an enclosure actuator message requesting controller data
    Given that SSPL is running
    When I send in the enclosure actuator message to request the current "ENCL:enclosure:fru:controller" data with instance id "1"
    Then I get the controller JSON response message

Scenario: Send SSPL an enclosure actuator message requesting temperature sensor data for all sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:temperature" data for "*" sensor
	Then I get the sensor JSON response message for "*" "Temperature" sensor

Scenario: Send SSPL an enclosure actuator message requesting temperature sensor data for specific sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:temperature" data for "CPU Temperature-Ctlr B" sensor
	Then I get the sensor JSON response message for "CPU Temperature-Ctlr B" "Temperature" sensor

Scenario: Send SSPL an enclosure actuator message requesting voltage sensor data for all sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:voltage" data for "*" sensor
	Then I get the sensor JSON response message for "*" "Voltage" sensor

Scenario: Send SSPL an enclosure actuator message requesting voltage sensor data for specific sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:voltage" data for "Capacitor Pack Voltage-Ctlr B" sensor
	Then I get the sensor JSON response message for "Capacitor Pack Voltage-Ctlr B" "Voltage" sensor

Scenario: Send SSPL an enclosure actuator message requesting current sensor data for all sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:current" data for "*" sensor
	Then I get the sensor JSON response message for "*" "Current" sensor

Scenario: Send SSPL an enclosure actuator message requesting current sensor data for specific sensor
	Given that SSPL is running
	When I send in the enclosure actuator request to get the current "ENCL:enclosure:sensor:current" data for "Current 12V Rail Loc: right-PSU" sensor
	Then I get the sensor JSON response message for "Current 12V Rail Loc: right-PSU" "Current" sensor

Scenario: Send SSPL a psu actuator message requesting psu data
	Given that SSPL is running
	When I send in the psu sensor message to request the psu "ENCL:enclosure:fru:psu" data
	Then I get the psu actuator JSON response message for psu instance "*"
	
Scenario: Send SSPL an Enclosure SAS Port message requesting sas port status data
	Given that SSPL is running
	When I send Enclosure SAS Port message to request the current "enclosure:interface:sas" data
	Then I get the Enclosure SAS ports JSON response message
