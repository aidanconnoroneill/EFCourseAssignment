import csv
import os
import click

from ortools.sat.python import cp_model


# CPModel
class ClassesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, course_assignments, courses, students, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._course_assignments = course_assignments
        self._students = students
        self._courses = courses
        self._solutions = set(sols)
        self._solution_count = 0

    def OnSolutionCallback(self):
        self._solution_count += 1
        if self._solution_count in self._solutions:
            print('Solution %i' % self._solution_count)
            for s in self._students:
                for c in self._courses:
                    if self.Value(self._course_assignments[(c, s)]):
                        print('  Student %i has class %i' % (s, c))
            self.StopSearch()

    def solution_count(self):
        return self._solution_count


# Gets the weight of a course given its ranking and whether or not to use the exponential ranking system
def get_course_weight(pos, is_exp):
    if pos is None:
        return -1
    if (is_exp):
        return 2**(5 - pos)
    else:
        if pos == 1:
            return 5
        if pos == 2:
            return 4
        if pos == 3:
            return 3
        if pos == 4:
            return 2
        if pos == 5:
            return 1
    return -1


# Gets the period associated with a classname.  Classnames should include "P1, P2, P3 or P4" at the beginning
def get_period(word):
    period = word.split()[0]
    if period == 'P1':
        return 1
    if period == 'P2':
        return 2
    if period == 'P3':
        return 3
    if period == 'P4':
        return 4
    return -1


# Returns the number of stars associated with a ranking
def get_num_stars(rank):
    if rank is None:
        return ""
    ret = ""
    for i in range(0, rank):
        ret += '!'
    return ret


# Parse the data in the csv into a bunch of useful maps
def read_data(filename, is_exp):
    count = 0
    course_hashes_to_names = {}
    students = []
    full_mapping = {}
    students_to_picks = {}
    student_hashes_to_names = {}

    courses = []

    num_courses_per_period = [0, 0, 0, 0]
    first_line = []

    student_course_to_student_rank = {}
    periods_to_courses = [[], [], [], []]
    count_students_per_period = [0, 0, 0, 0]

    lst_delinquent_ids = []

    with open(filename, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')

        for line in csv_reader:
            # Read in first line of courses
            if count == 0:
                first_line = line
                count += 1
                for i in range(3, len(line)):
                    if (len(line[i]) < 3):
                        continue
                    num_courses_per_period[get_period(line[i]) - 1] += 1
                    course_hashes_to_names.update({hash(line[i]): line[i]})
                    courses.append(hash(line[i]))
                    periods_to_courses[get_period(line[i]) - 1].append(
                        hash(line[i]))
                continue
            # Get the full student
            full_student = (line[0], line[1], line[2])
            student_id = hash(full_student)
            student_hashes_to_names.update({student_id: full_student})
            students.append(student_id)

            periods = []
            index_in_line = 3
            is_delinquent = True
            for period in range(1, 5):
                picks = []
                flag = False
                for course in range(0, num_courses_per_period[period - 1]):
                    pick_rank = None
                    if line[index_in_line] != '' and line[index_in_line] != ' ':
                        pick_rank = int(line[index_in_line])
                        flag = True
                    weight = get_course_weight(pick_rank, is_exp)
                    full_mapping.update({
                        (hash(first_line[index_in_line]), student_id):
                        weight
                    })
                    student_course_to_student_rank.update({
                        (hash(first_line[index_in_line]), student_id):
                        pick_rank
                    })
                    if weight != -1:
                        picks.append(hash(first_line[index_in_line]))
                    index_in_line += 1
                periods.append(picks)
                if flag:
                    count_students_per_period[period - 1] += 1
                    is_delinquent = False
            students_to_picks.update({student_id: periods})
            if is_delinquent:
                lst_delinquent_ids.append(student_id)

        return (course_hashes_to_names, courses, students, full_mapping,
                students_to_picks, student_hashes_to_names,
                student_course_to_student_rank, num_courses_per_period,
                periods_to_courses, count_students_per_period,
                lst_delinquent_ids)


@click.command()
@click.option(
    '--exp_weighting',
    '-e',
    default=None,
    help='Whether or not you want to use the exponential weighting scheme')
def main(exp_weighting=False):
    exponential_weighting = False
    if (exp_weighting is not None):
        exponential_weighting = True

    data_path = 'CoursePicks.csv'  # Data directory
    parsed_data = read_data(data_path, exponential_weighting)
    course_hashes_to_names = parsed_data[0]
    courses = parsed_data[1]
    students = parsed_data[2]
    mapping = parsed_data[3]
    students_to_picks = parsed_data[4]
    student_hashes_to_names = parsed_data[5]
    student_course_to_student_rank = parsed_data[6]
    num_courses_per_period = parsed_data[7]
    periods_to_courses = parsed_data[8]
    count_students_per_period = parsed_data[9]
    lst_delinquent_ids = parsed_data[10]

    model = cp_model.CpModel()
    course_match = {}
    # Set up model
    for c in courses:
        for s in students:
            course_match[(c, s)] = model.NewBoolVar(
                'course%iis assigned to %i' % (c, s))
    # Add constraints
    for c in courses:
        for s in students:
            if student_course_to_student_rank[(c, s)] is None:
                model.Add(course_match[(c, s)] == 0)

    for s in students_to_picks:
        for period in range(0, 4):
            picks = students_to_picks[s][period]
            if (len(picks) != 0):
                model.Add(sum(course_match[(c, s)] for c in picks) == 1)

    courses_to_min_max = {}
    for i in range(0, 4):
        courses_in_period = periods_to_courses[i]
        expected_students = int(count_students_per_period[i] /
                                len(courses_in_period))
        for c in courses_in_period:
            course_max = expected_students + 1
            course_min = expected_students
            courses_to_min_max.update({c: (course_max, course_min)})
            model.Add(
                sum(course_match[(c, s)] for s in students) <= course_max)
            model.Add(
                sum(course_match[(c, s)] for s in students) >= course_min)

    # Have google's ortools work its magic
    model.Maximize(
        sum(course_match[(c, s)] * mapping[(c, s)] for c in courses
            for s in students))

    solver = cp_model.CpSolver()

    solver.Solve(model)

    # Write human-readable solution to file results.csv
    num_students = len(students)

    if not os.path.exists('results'):
        os.mkdir('results')

    cur_filename = 'results/' + 'results.csv'
    f = open(cur_filename, 'w')

    course_enrollment = {}
    for c in courses:
        num_students_in_course = 0
        for s in students:
            if solver.Value(course_match[c, s]) == 1:
                num_students_in_course += 1

        course_enrollment.update({c: num_students_in_course})

    for student_hash in student_hashes_to_names:
        student_name = student_hashes_to_names[student_hash]
        str_to_write = student_name[0] + ',' + student_name[
            1] + ',' + student_name[2] + ','
        lst_courses = ["Teaching", "Teaching", "Teaching", "Teaching"]
        if student_hash not in lst_delinquent_ids:
            for c in courses:
                num_students_in_course = course_enrollment[c]
                if solver.Value(course_match[(c, student_hash)]) == 1:
                    course_name = course_hashes_to_names[c]
                    course_period = get_period(course_name)
                    lst_courses[
                        course_period - 1] = course_name + get_num_stars(
                            student_course_to_student_rank[(c, student_hash)])
                if num_students_in_course == courses_to_min_max[c][1] and (
                        student_hash in lst_delinquent_ids):
                    course_name = course_hashes_to_names[c]
                    course_period = get_period(course_name)
                    if lst_courses[course_period - 1] == "Teaching":

                        # print("Here:" + str_to_write + str(course_period))
                        lst_courses[course_period -
                                    1] = course_name + get_num_stars(
                                        student_course_to_student_rank[
                                            (c, student_hash)])
                        new_enrollment_num = num_students_in_course + 1
                        course_enrollment.update({c: new_enrollment_num})
        else:

            for period in range(1, 5):
                course_assignment = lst_courses[period - 1]
                if course_assignment == "Teaching":
                    for c in courses:
                        num_students_in_course = course_enrollment[c]
                        course_period = get_period(course_hashes_to_names[c])
                        if num_students_in_course <= courses_to_min_max[c][
                                0] + 1 and course_period == period:
                            lst_courses[period - 1] = course_hashes_to_names[c]
                            break

        for i in range(0, 4):
            str_to_write += lst_courses[i]
            str_to_write += ', '
        str_to_write += '\n'
        f.write(str_to_write)
    f.write('\n')
    for c in courses:
        course_name = course_hashes_to_names[c]
        f.write(course_name + ",\n")
        for student_hash in student_hashes_to_names:
            if solver.Value(course_match[(c, student_hash)]) == 1:
                student_name = student_hashes_to_names[student_hash]
                str_to_write = student_name[0] + ',' + student_name[
                    1] + ',' + student_name[2] + ','
                f.write(str_to_write + "\n")
        f.write('\n')

    for c in courses:

        course_name = course_hashes_to_names[c]
        num_students_in_this_course = str(course_enrollment[c])
        f.write(course_name + "," + num_students_in_this_course + ",\n")

    f.close()
    print('Done writing')

    # Statistics.
    print('Results saved to {}'.format(cur_filename))
    print()
    print('Statistics')
    print('  - conflicts       : %i' % solver.NumConflicts())
    print('  - branches        : %i' % solver.NumBranches())
    print('  - Value of courses = %i' % solver.ObjectiveValue())

    print('  - wall time       : %f s' % solver.WallTime())


if __name__ == "__main__":
    main()
