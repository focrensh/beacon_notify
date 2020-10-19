# F5 Beacon Notification
This is an example of using the results of a F5 Beacon API call to general alerts and notifications. The repo builds a docker container that can be run to handle the polling and sending of notifications. It utilizes [Apprise](https://github.com/caronc/apprise) for sending the notifications. This allows you to update the configuration to send the alerts to any integrations supposed by Apprise.

![Teams output](./images/teams_example.png | width=300)

## Workflow
* The container will poll the F5 Beacon API on an interval set in the `beacon_config.yaml` file.
* When an application is in a state included in the **alert_state** parameter within the `beacon_config.yaml` file, it will take action.
* The container will then send notficiations to the destinations listed in the `config.yaml` file. This file controls the settings for **Apprise**.
* If an app is in an **alert_state**, it will not notify again until the **repeatMessage** timer has been met that is set within the `beacon_config.yaml` file. Once that timer is met, it will be considered a new alert again.

## Example
1. Clone the repo and change to the directory
1. Update the `beacon_config.yaml` file to match the settings you would like to use.
   * **apps**: which applications you would like to notify for.
   * **checkInterval**: How often should it check Beacon for status
   * **repeatMessage**: How long it should wait before re-sending if the status has not changed.
   * **alert_states**: which states you would like notifications for (currently only Critical and Warning are supported).
   * **clear_states**: which states would like to cause a reset in timing for **repeatMessage**. (Currently only Health is supported)

1. Update the **urls** in `config.yaml` with the destinations you would like notifications sent to. Please note the [Apprise](https://github.com/caronc/apprise) docs for available options. The example includes a template for msteams.
1. Build the container

   `docker build -t beacon_notify .`

1. Run the docker container and pass Beacon credentials as environment variables:

   `docker run -d -v $(pwd):/usr/src/app -e BEACON_UN='<email>' -e BEACON_PW='<password>' -e BEACON_ACCT='<account>'  beacon_notify`
