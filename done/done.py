""" Show a toggle which lets students mark things as done."""

import re
import uuid

from django.utils.translation import ugettext as _
import pkg_resources
from xblock.core import XBlock
from xblock.fields import Boolean, DateTime, Float, Scope, String
from web_fragments.fragment import Fragment


from xblockutils.studio_editable import StudioEditableXBlockMixin

from lms.djangoapps.certificates.api import generate_user_certificates


def resource_string(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


@XBlock.wants("settings")
@XBlock.needs("i18n")
class DoneXBlock(StudioEditableXBlockMixin, XBlock):
    """
    Show a toggle which lets students mark either sections or whole courses as done.
    """

    done = Boolean(
        scope=Scope.user_state,
        help="Is the student done?",
        default=False
    )

    align = String(
        display_name=_("Alignment"),
        scope=Scope.content,
        help="Align left/right/center",
        default="left"
    )

    done_scope = String(
        display_name=_("Scope"),
        scope=Scope.content,
        help="Scope of completion.  Marking a 'Course' scope Done component complete triggers course grading.",
        values=[
            {"display_name": "Section", "value": "block"},
            {"display_name": "Course", "value": "course"}
        ],
        default="block"
    )

    button_text_before = String(
        display_name=_("Button text (incomplete)"),
        scope=Scope.content,
        help="Text displayed on the button before completion",
        default="Mark as complete"
    )

    button_text_after = String(
        display_name=_("Button text (complete)"),
        scope=Scope.content,
        help="Text displayed on the button after completion",
        default="Mark as incomplete"
    )

    instructions = String(
        display_name=_("Instructions"),
        scope=Scope.content,
        help="Additional instruction or other text displayed below the button",
        default=""
    )

    editable_fields = [
        'align', 'done_scope', 'button_text_before', 
        'button_text_after', 'instructions'
    ]

    has_score = True

    # pylint: disable=unused-argument
    @XBlock.json_handler
    def toggle_button(self, data, suffix=''):
        """
        Ajax call when the button is clicked. Input is a JSON dictionary
        with two fields: a boolean `done` and a `scope` which can be either
        `block` or `course`. This will save this in the
        XBlock field, and then issue an appropriate grade.
        If `scope` is `course` then request a grade on the entire course. 
        """
        success = 'failure'
        anon_id = self.runtime.anonymous_student_id
        student = self.runtime.get_real_user(anon_id) if self.runtime.get_real_user is not None else None

        if 'done' in data:

            # don't allow course-scoped to be "un-done"
            if not data['done'] and self.done == 1 and self.done_scope == 'course':
                return {'state': self.done, 'success': success}
            else:
                self.done = data['done']
                if data['done']:
                    grade = 1
                else:
                    grade = 0
                grade_event = {'value': grade, 'max_value': 1}
                if student:
                    self.runtime.publish(self, 'grade', grade_event)
                    # This should move to self.runtime.publish, once that pipeline
                    # is finished for XBlocks.
                    self.runtime.publish(self, "edx.done.toggled", {'done': self.done})
                    success = 'success'

                    if data['scope'] == 'course' and grade == 1:
                        # request grading on whole course if in the LMS with a real student
                        course_key = self.runtime.course_id
                        cert_status = generate_user_certificates(
                            student, course_key, course=None, insecure=False, 
                            generation_mode='batch', forced_grade=None
                        )
                        success = 'success'

        return {'state': self.done, 'success': success}

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        The primary view of the DoneXBlock, shown to students
        when viewing courses.
        """

        def css_content_escape(inputstr):
            """
            escape strings for CSS content attribute
            """
            # https://stackoverflow.com/a/25699953
            css_content_re = r'''['"\n\\]'''
            return re.sub(css_content_re, lambda m: '\\{:X} '.format(ord(m.group())), inputstr)

        button_text_before = css_content_escape(self.button_text_before)
        button_text_after = css_content_escape(self.button_text_after)
        status_button_text = self.button_text_before if self.done else self.button_text_after
        # course-scoped completions cannot be un-done
        disabled_attr = "disabled" if self.done_scope == 'course' and self.done else ""

        html_resource = resource_string("static/html/done.html")
        html = html_resource.format(done=self.done,
                                    id=uuid.uuid1(0),
                                    button_text_before=button_text_before,
                                    button_text_after=button_text_after,
                                    button_text=status_button_text,
                                    instructions=self.instructions,
                                    disabled=disabled_attr,
                                    )

        (unchecked_png, checked_png) = (
            self.runtime.local_resource_url(self, x) for x in
            ('public/check-empty.png', 'public/check-full.png')
        )

        frag = Fragment(html)
        frag.add_css(resource_string("static/css/done.css"))
        frag.add_javascript(resource_string("static/js/src/done.js"))
        frag.initialize_js("DoneXBlock", {'state': self.done,
                                          'unchecked': unchecked_png,
                                          'checked': checked_png,
                                          'align': self.align.lower(),
                                          'scope': self.done_scope})
        return frag

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("DoneXBlock",
             """<vertical_demo>
                  <done done_scope="block" align="left"> </done>
                  <done done_scope="block" align="right"> </done>
                  <done done_scope="block" align="center"> </done>
                  <done done_scope="course" align="left" 
                    button_text_before="Complete course" button_text_after="Course completed!"> </done>
                  <done done_scope="block" align="left" instructions="Some instructions"> </done>
                </vertical_demo>
             """),
        ]

    # Everything below is stolen from
    # https://github.com/edx/edx-ora2/blob/master/apps/openassessment/
    #        xblock/lms_mixin.py
    # It's needed to keep the LMS+Studio happy.
    # It should be included as a mixin.

    display_name = String(
        default="Completion", scope=Scope.content,
        help="Display name"
    )

    start = DateTime(
        default=None, scope=Scope.content,
        help="ISO-8601 formatted string representing the start date "
             "of this assignment. We ignore this."
    )

    due = DateTime(
        default=None, scope=Scope.content,
        help="ISO-8601 formatted string representing the due date "
             "of this assignment. We ignore this."
    )

    weight = Float(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": .1},
        scope=Scope.content
    )

    def has_dynamic_children(self):
        """Do we dynamically determine our children? No, we don't have any.
        """
        return False

    def max_score(self):
        """The maximum raw score of our problem.
        """
        return 1
