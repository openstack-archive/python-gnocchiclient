#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from cliff import show


class CliStatusShow(show.ShowOne):
    def take_action(self, parsed_args):
        status = self.app.client.status.get()

        nb_metric = len(status['storage']['measures_to_process'])
        nb_measures = (
            sum(status['storage']['measures_to_process'].values())
        )

        return self.dict2columns({
            "storage/total number of measures to process": nb_measures,
            "storage/number of metric having measures to process": nb_metric,
        })
