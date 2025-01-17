import csv
import pandas as pd
import math
from ortools.sat.python import cp_model


class Student:
    def __init__(self, first, last, class_preferences):
        self.first = first
        self.last = last
        self.class_preferences = class_preferences
        self.classes = list()

    def set_name(self, first, last):
        self.first = first
        self.last = last

    def set_class_preferences(self, class_preferences):
        self.class_preferences = class_preferences

    def get_class_preferences(self):
        return self.class_preferences

    def get_classes(self):
        return self.classes

    def add_class(self, new_class):
        self.classes.append(new_class)

    def remove_class(self, old_class):
        self.classes.remove(old_class)

    def get_value(self):
        total_value = 0
        for class_, valuation in self.class_preferences:
            if class_ in self.classes:
                total_value += valuation
        return total_value

    def get_value_of_course(self, course):
        for class_, valuation in self.class_preferences:
            if course == class_:
                return valuation
        return 0

    def EF1(self, other_courses):
        best_to_steal = 0
        best_course = None
        value_other = 0
        for other_course in other_courses:
            for class_, valuation in self.class_preferences:
                if other_course == class_:
                    value_other += valuation
                    if valuation > best_to_steal:
                        best_to_steal = valuation
                        best_course = other_course
        my_value = self.get_value()
        return (my_value + best_to_steal >= value_other - best_to_steal, best_course)

    def __hash__(self):
        return hash((self.first, self.last))


class Course:
    def __init__(self, args):
        self.period = args[0]
        self.name = args[1]

    def set_period(self, period):
        self.period = period

    def get_period(self):
        return self.period

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.period == other.period

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return str(self.name)


def read_data(filename):
    data = pd.read_csv(filename)
    print(data.head())
    courses = []
    students = []
    for col in data.columns:
        if col == "Student" or col == "Surname" or col == "Family":
            continue
        courses.append(Course(col.split(" ", 1)))

    for _, row in data.iterrows():
        first = row["Student"]
        last = row["Surname"]
        course_preferences = []
        for c in range(len(row)):
            key = data.columns[c]
            try:
                val = int(row[c])
                if key.startswith("P") and not math.isnan(val):  # and val < 5:
                    course_preferences.append(
                        (Course(key.split(" ", 1)), 5-val))
            except:
                pass
        students.append(Student(first, last, course_preferences))
    return (courses, students)


def main():
    courses, students = read_data("CoursePicks.csv")
    course_hashes = []
    student_hashes = []
    for c in courses:
        course_hashes.append(hash(c))
    for s in students:
        student_hashes.append(hash(s))
    model = cp_model.CpModel()
    course_match = {}
    # Set up model

    for c in course_hashes:
        for s in student_hashes:
            course_match[(c, s)] = model.NewBoolVar(
                'course %i is assigned to %i' % (c, s))
    # Add constraints
    for c in course_hashes:
        for i in range(len(student_hashes)):
            s = students[i]
            found = False
            for class_preference in s.get_class_preferences():
                if c == hash(class_preference[0]):
                    found = True
                    break
            if not found:
                model.Add(course_match[(c, student_hashes[i])] == 0)

    for s in students:
        for period in ["P1", "P2", "P3", "P4"]:
            okay_in_period_for_student = []
            for c in s.get_class_preferences():
                if c[0].get_period() == period:
                    okay_in_period_for_student.append(hash(c[0]))

            model.Add(sum(course_match[(c, hash(s))]
                          for c in okay_in_period_for_student) <= 1)

    student_values = {}
    for s in students:
        for c in courses:
            student_values[(hash(c), hash(s))] = s.get_value_of_course(c)

    model.Maximize(
        sum(course_match[(c, s)] * student_values[(c, s)] for c in course_hashes
            for s in student_hashes))

    for c in course_hashes:
        model.Add(sum(course_match[(c, s)] for s in student_hashes) <= 5)
        # model.Add(sum(course_match[(c, s)] for s in student_hashes) >= 7)

    solver = cp_model.CpSolver()

    solver.Solve(model)

    for ch in course_hashes:
        for sh in student_hashes:
            if solver.Value(course_match[(ch, sh)]) == 1:
                student = None
                course = None
                for c in courses:
                    if hash(c) == ch:
                        course = c
                        break
                for s in students:
                    if hash(s) == sh:
                        student = s
                        break
                student.add_class(course)

    changed = True
    while (changed):
        changed = False
        for i in range(len(students)):
            for j in range(i + 1, len(students)):
                student1 = students[i]
                student2 = students[j]
                student1_envy, best_course1 = student1.EF1(
                    student2.get_classes())
                student2_envy, best_course2 = student2.EF1(
                    student1.get_classes())

                if not student1_envy:
                    student1.add_class(best_course1)
                    student2.remove_class(best_course1)
                    ut_loss = student2.get_value_of_course(
                        best_course1) - student1.get_value_of_course(best_course1)
                    print("made, ut lost", ut_loss)
                    changed = True
                elif not student2_envy:
                    student2.add_class(best_course2)
                    student1.remove_class(best_course2)
                    ut_loss = student1.get_value_of_course(
                        best_course2) - student2.get_value_of_course(best_course2)
                    print("made, ut lost", ut_loss)
                    changed = True
    print('Done writing')

    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - Value of courses = %i' % solver.ObjectiveValue())

    print('  - wall time       : %f s' % solver.WallTime())


if __name__ == "__main__":
    main()
