import numpy as np
from copy import copy


class LocatedTensor:
    """
    the class implements a pair of an N dimensional tensor and a vector which contained N element
    """

    # ----------------- Class creators ----------------- #

    def __init__(self, corner, value, axis_magic=False):
        """
        :param corner: (tuple) vector of the lower left corner of the tensor location in N dimensional space
        :param value: (ndarray) value of the tensor
        :param axis_magic: (boolean) changes axes in such way that str(tensor) looks like str(ndarray)
        """
        assert isinstance(corner, tuple), "Init exception: arg corner must be a TUPLE"
        assert isinstance(value, np.ndarray), "Init exception: arg value must be an NDARRAY"
        assert len(corner) == value.ndim, "Init exception: LEN of corner and DIM of value must be equal"
        self.__corner = np.array(corner)
        self.__value = np.flip(value.copy().T, axis=range(1, value.ndim)) if axis_magic else value.copy()

    @classmethod
    def zeros(cls, corner=None, *, dim):
        """ alternative creator, which fills tensor with zeros values """
        if corner is None:
            corner = tuple(np.zeros(len(dim)))  # set default value if it's necessary
        value = np.zeros(dim)
        return cls(corner, value)

    # ----------------- Values ----------------- #

    def __getitem__(self, key):
        """ direct access to tensor's value (getter) BY LOCAL POINT """
        return self.__value[key]

    def __setitem__(self, key, value):
        """ direct access to tensor's value (setter) BY LOCAL POINT """
        self.__value[key] = value

    def get_global(self, point, default=None):
        """
        access to tensor's value (getter) BY GLOBAL POINT
        return default if point is out of range (handling not exists exception)
        """

        local_point = self.point_to_local(point)
        point_is_within = ((np.zeros(self.ndim) <= local_point) & (local_point < np.array(self.dim))).all()

        if point_is_within:
            return self[local_point]
        else:
            return default

    def set_global(self, point, value):
        """
        access to tensor's value (getter) BY GLOBAL POINT
        return ERROR if point is out of range (no handling not exists exception)
        """

        local_point = self.point_to_local(point)
        self[local_point] = value

    # ----------------- Points ----------------- #

    def point_to_local(self, point):
        """ to get a local location of the global point """
        return tuple(np.array(point) - self.corner)

    def point_to_global(self, point):
        """
        to get a global location of the local point
        """
        return tuple(np.array(point) + self.corner)

    @property
    def all_points_local(self):
        """ returns list of all indexes of tensor (LOCAL POINTS) """
        return list(np.ndindex(self.dim))

    @property
    def all_points_global(self):
        """ returns list of all indexes of tensor (GLOBAL POINTS) """
        return [self.point_to_global(point) for point in self.all_points_local]

    @property
    def not_null_points_local(self):
        """ does the same that all_points, but it excludes zero values (LOCAL POINTS) """
        return list(zip(*np.nonzero(self.__value != 0)))

    @property
    def not_null_points_global(self):
        """ does the same that all_points, but it excludes zero values (GLOBAL POINTS) """
        return [self.point_to_global(point) for point in self.not_null_points_local]

    # ----------------- Attributes ----------------- #

    @property
    def dim(self):
        """ shortcut for the shape """
        return self.__value.shape

    @property
    def ndim(self):
        """ shortcut for the number of dimensional """
        return self.__value.ndim

    @property
    def corner(self):
        """ shortcut for corner (left-bottom) param """
        return self.__corner

    @property
    def opp_corner(self):
        """ vector of the opposite corner (right-top) of the tensor """
        return self.corner + self.dim - 1

    # ----------------- Math Operations ----------------- #

    @classmethod
    def __base_ops(cls, T1, T2, ops):
        """
        base internal function that can use for create the binary operations, such as union and subtract.
        """

        # create blank result tensor
        corner = tuple(np.vstack((T1.corner, T2.corner)).min(axis=0))
        dim = tuple(np.vstack((T1.opp_corner, T2.opp_corner)).max(axis=0) - corner + 1)
        result = cls.zeros(corner, dim=dim)

        # calculating values for result tensor:
        for global_point in set(T1.all_points_global) | set(T2.all_points_global):  # or result.all_points_global ?
            t1_value = T1.get_global(global_point, 0)
            t2_value = T2.get_global(global_point, 0)
            result.set_global(global_point, ops(t1_value, t2_value))

        return result

    def __add__(self, t):
        """ operation of addition two tensors """
        return self.__base_ops(self, t, lambda a, b: a + b)

    def __sub__(self, t):
        """ operation of subtraction two tensors"""
        return self.__base_ops(self, t, lambda a, b: a - b)

    def fill(self, value):
        """ set all not null points with given value """
        result = copy(self)
        for point in result.not_null_points_local:
            result[point] = value
        return result

    def minimum(self, threshold):
        """ fill with zero all values which don't satisfy the minimum  """
        result = copy(self)
        for point in result.not_null_points_local:
            value = result[point]
            if value < threshold:
                result[point] = 0
        return result

    def hollow(self):
        """
        [[1 1 1]    [[1 1 1]
         [1 1 1] =>  [1 0 1]
         [1 1 1]]    [1 1 1]]
        """
        result = copy(self)
        dim = self.dim
        ndim = self.ndim
        for point in result.all_points_local:
            if self[point] != 0:  # count only for non-zero cell
                cnt = 0
                for i in range(ndim):  # step for each dimensional [0, 1, 2]
                    offset = np.zeros(ndim)  # blank point [0, 0, 0]
                    offset[i] = 1  # x-neighbor [1, 0, 0], y-neighbor [0, 1, 0], z-neighbor [0, 0, 1]
                    for sign in [1, -1]:  # for opposite direction
                        n = tuple(np.int64(np.array(point) + (offset * sign)))  # point for neighbor with shift
                        if 0 <= n[i] < dim[i]:  # check boundaries
                            cnt += 0 if self[n] == 0 else 1  # check neighbor
                if cnt == len(point) * 2:  # max count of neighbors is ndim * 3 (4 for 2d, 6 for 3d)
                    result[point] = 0  # set with zero if cell has max count of neighbors
        return result

    def num_alive(self, global_point):
        """ count the number of the alive (non-zero) neighbors (include diagonal neighbors!) """
        def get_neighbors(point, start=True):  # let point = (1, 2, 3)
            result = []  # list for all possible neighbors
            for i in [0, 1, -1]:  # all possible shifts, see for 1
                if len(point) > 1:
                    for tail in get_neighbors(point[1:], False):  # all possible tails, let see for (3, 3)
                        neighbor = (point[0] + i, *tail)  # (1 + 1, (3, 3)) => (2, 3, 3)
                        result.append(neighbor)
                else:
                    neighbor = (point[0] + i,)  # for point (1,) we get 3 options of neighbors => (1,) (2,) (0,)
                    result.append(neighbor)
            if start:
                del result[0]  # delete origin point that isn't neighbor for itself
            return result

        num = 0
        for neighbor_point in get_neighbors(global_point):
            if self.get_global(neighbor_point, 0) != 0:  # we use 0 as default for getting out of range
                num += 1
        return num

    # ----------------- Others ----------------- #

    def __copy__(self):
        """ implementation of copy process """
        return LocatedTensor(tuple(self.__corner.copy()), self.__value.copy())

    def __str__(self):
        """
        string representation of an object
        (works only for 2 and 3 dims so far)
        """
        def prepare_convert(array):
            return np.flip(array.transpose(), axis=tuple(range(array.ndim - 1)))

        def str_2d_matrix(matrix):
            rows = str(matrix).split("\n")
            rows.insert(0, "Y ")
            rows.insert(1, "^ ")
            rows[2:] = ["| " + row for row in rows[2:]]
            rows.append("+" + "-" * (len(rows[-1])) + " > X")
            result = "\n".join(rows)
            return result

        def str_3d_tensor(tensor):
            matrices = str(tensor).split("\n\n")
            matrices = [str_2d_matrix(matrix) for matrix in matrices]
            matrices = "\n\n".join(matrices)
            matrices = matrices.split("\n")
            matrices.insert(0, "Z")
            matrices.insert(1, "^")
            matrices[2:] = ["| " + matrix for matrix in matrices[2:]]
            result = "\n".join(matrices)
            return result

        result = prepare_convert(self.__value)

        if self.__value.ndim == 3:
            result = str_3d_tensor(result)
        elif self.__value.ndim == 2:
            result = str_2d_matrix(result)

        return "{" + str(self.corner) + ",\n" + result + "}"