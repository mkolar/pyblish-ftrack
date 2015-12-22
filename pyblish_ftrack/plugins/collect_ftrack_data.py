import os
import json
import base64
import ftrack
import collections
import pyblish.api


@pyblish.api.log
class CollectFtrackData(pyblish.api.Selector):

    """Collects ftrack data from FTRACK_CONNECT_EVENT
        Arguments:
            version (int): version number of the publish
    """

    order = pyblish.api.Selector.order
    hosts = ['*']
    version = (0, 1, 0)

    def process(self, context):

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

        ftrack_data = self.get_context(task)

        # set ftrack data
        context.data['ftrackData'] = dict(ftrack_data)

        self.log.info('Found ftrack data: \n\n%s' % ftrack_data)

    # def get_data(self, taskid):
    #
    #     task_codes = {
    #         'Animation': 'anim',
    #         'Layout': 'layout',
    #         'FX': 'fx',
    #         'Compositing': 'comp',
    #         'Motion Graphics': 'mograph',
    #         'Lighting': 'light',
    #         'Modeling': 'geo',
    #         'Rigging': 'rig',
    #         'Art': 'art',
    #     }
    #
    #     try:
    #         task = ftrack.Task(id=taskid)
    #     except ValueError:
    #         task = None
    #
    #     parents = task.getParents()
    #     project = ftrack.Project(task.get('showid'))
    #     taskType = task.getType().getName()
    #     entityType = task.getObjectType()
    #
    #     ctx = {
    #         'Project': {
    #             'name': project.get('fullname'),
    #             'code': project.get('name'),
    #             'id': task.get('showid'),
    #             'root': project.getRoot(),
    #         },
    #         entityType: {
    #             'type': taskType,
    #             'name': task.getName(),
    #             'id': task.getId(),
    #             'code': task_codes.get(taskType, None)
    #         }
    #     }
    #
    #     for parent in parents:
    #         tempdic = {}
    #         if parent.get('entityType') == 'task' and parent.getObjectType():
    #             objectType = parent.getObjectType()
    #             tempdic['name'] = parent.getName()
    #             tempdic['description'] = parent.getDescription()
    #             tempdic['id'] = parent.getId()
    #             if objectType == 'Asset Build':
    #                 tempdic['type'] = parent.getType().get('name')
    #                 objectType = objectType.replace(' ', '_')
    #
    #             ctx[objectType] = tempdic
    #
    #     return ctx

    def get_context(self, entity):

        task_codes = {
                'Animation': 'anim',
                'Layout': 'layout',
                'FX': 'fx',
                'Compositing': 'comp',
                'Motion Graphics': 'mograph',
                'Lighting': 'light',
                'Modeling': 'geo',
                'Rigging': 'rig',
                'Art': 'art',
            }

        entityName = entity.getName()
        entityId = entity.getId()
        entityType = entity.getObjectType()
        entityDescription = entity.getDescription()

        hierarchy = entity.getParents()

        ctx = collections.OrderedDict()

        if entity.get('entityType') == 'task' and entityType == 'Task':
            taskType = entity.getType().getName()
            entityDic = {
                'type': taskType,
                'name': entityName,
                'id': entityId,
                'code': task_codes.get(taskType, None),
                'description': entityDescription
            }
        elif entity.get('entityType') == 'task':
            entityDic = {
                'name': entityName,
                'id': entityId,
                'description': entityDescription
            }

        ctx[entityType] = entityDic

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

            ctx[objectType] = tempdic

        return ctx
