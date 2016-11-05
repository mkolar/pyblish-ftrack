import os
import json
import base64
import ftrack
import collections
import pyblish.api


@pyblish.api.log
class CollectFtrackData(pyblish.api.ContextPlugin):

    """Collects ftrack data from FTRACK_CONNECT_EVENT
    """

    order = pyblish.api.CollectorOrder
    hosts = ['*']

    def process(self, context):

        # accounting for preexiting data
        if "ftrackData" in context.data:
            data = context.data["ftrackData"]
            self.log.info('Found ftrack data: \n\n%s' % data)
            return

        # getting task id
        taskid = ''
        try:
            decodedEventData = json.loads(
                base64.b64decode(
                    os.environ.get('FTRACK_CONNECT_EVENT')
                )
            )

            taskid = decodedEventData.get('selection')[0]['entityId']
        except:
            taskid = os.environ['FTRACK_TASKID']

        task = ftrack.Task(taskid)

        ftrack_data = self.get_data(task)

        # set ftrack data
        context.data['ftrackData'] = dict(ftrack_data)

        self.log.info('Found ftrack data: \n\n%s' % ftrack_data)

    def get_data(self, entity):

        entityName = entity.getName()
        entityId = entity.getId()
        entityType = entity.getObjectType()
        entityDescription = entity.getDescription()

        hierarchy = entity.getParents()

        data = collections.OrderedDict()

        if entity.get('entityType') == 'task' and entityType == 'Task':
            taskType = entity.getType().getName()
            entityDic = {
                'type': taskType,
                'name': entityName,
                'id': entityId,
                'description': entityDescription
            }
        elif entity.get('entityType') == 'task':
            entityDic = {
                'name': entityName,
                'id': entityId,
                'description': entityDescription
            }

        data[entityType] = entityDic

        for ancestor in hierarchy:
            tempdic = {}
            if isinstance(ancestor, ftrack.Component):
                # Ignore intermediate components.
                continue

            tempdic['name'] = ancestor.getName()
            tempdic['id'] = ancestor.getId()

            try:
                objectType = ancestor.getObjectType()
                tempdic['description'] = ancestor.getDescription()
            except AttributeError:
                objectType = 'Project'
                tempdic['description'] = ''

            if objectType == 'Asset Build':
                tempdic['type'] = ancestor.getType().get('name')
                objectType = objectType.replace(' ', '_')
            elif objectType == 'Project':
                tempdic['code'] = tempdic['name']
                tempdic['name'] = ancestor.get('fullname')
                tempdic['root'] = ancestor.getRoot()

            data[objectType] = tempdic

        return data
