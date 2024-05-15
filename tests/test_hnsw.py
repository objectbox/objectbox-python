import math
import numpy as np
import random
from common import *
from objectbox.query_builder import QueryBuilder


def _find_expected_nn(points: np.ndarray, query: np.ndarray, n: int):
    """ Given a set of points of shape (N, P) and a query of shape (P), finds the n points nearest to query. """

    assert points.ndim == 2 and query.ndim == 1
    assert points.shape[1] == query.shape[0]

    d = np.linalg.norm(points - query, axis=1)  # Euclidean distance
    return np.argsort(d)[:n]


def _test_random_points(
        num_points: int,
        num_query_points: int,
        seed: Optional[int] = None,
        distance_type: VectorDistanceType = VectorDistanceType.EUCLIDEAN,
        min_score: float = 0.5):
    """ Generates random points in a 2d plane; checks the queried NN against the expected. """

    vector_field_name = "vector_"+distance_type.name.lower()

    print(f"Test random points; Points: {num_points}, Query points: {num_query_points}, Seed: {seed}")

    k = 10

    if seed is not None:
        np.random.seed(seed)

    points = np.random.rand(num_points, 2).astype(np.float32)

    store = create_test_store()

    # Init and seed DB
    box = store.box(VectorEntity)

    print(f"Seeding DB with {num_points} points...")
    objects = []
    for i in range(points.shape[0]):
        object_ = VectorEntity()
        object_.name = f"point_{i}"
        setattr(object_, vector_field_name, points[i])
        objects.append(object_)
    box.put(*objects)
    print(f"DB seeded with {box.count()} random points!")

    assert box.count() == num_points

    # Generate a random list of query points
    query_points = np.random.rand(num_query_points, 2).astype(np.float32)

    # Iterate query points, and compare expected result with OBX result
    print(f"Running {num_query_points} searches...")
    for i in range(query_points.shape[0]):
        query_point = query_points[i]

        # Find the ground truth (brute force)
        expected_result = _find_expected_nn(points, query_point, k) + 1  # + 1 because OBX IDs start from 1
        assert len(expected_result) == k

        # Run ANN with OBX
        qb = box.query()
        qb.nearest_neighbors_f32(vector_field_name, query_point, k)
        query = qb.build()
        obx_result = [id_ for id_, score in query.find_ids_with_scores()]  # Ignore score
        assert len(obx_result) == k

        # We would like at least half of the expected results, to be returned by the search (in any order)
        # Remember: it's an approximate search!
        search_score = len(np.intersect1d(expected_result, obx_result)) / k
        assert search_score >= min_score  # TODO likely could be increased

    print(f"Done!")


def test_random_points():
        
    min_score = 0.5
    distance_type = VectorDistanceType.EUCLIDEAN
    _test_random_points(num_points=100, num_query_points=10, seed=10, distance_type=distance_type, min_score=min_score)
    _test_random_points(num_points=100, num_query_points=10, seed=11, distance_type=distance_type, min_score=min_score)
    _test_random_points(num_points=100, num_query_points=10, seed=12, distance_type=distance_type, min_score=min_score)
    _test_random_points(num_points=100, num_query_points=10, seed=13, distance_type=distance_type, min_score=min_score)
    _test_random_points(num_points=100, num_query_points=10, seed=14, distance_type=distance_type, min_score=min_score)
    _test_random_points(num_points=100, num_query_points=10, seed=15, distance_type=distance_type, min_score=min_score)

    # TODO: Cosine and Dot Product may result in 0 score


def _test_combined_nn_search(distance_type: VectorDistanceType = VectorDistanceType.EUCLIDEAN):

    store = create_test_store()

    box = store.box(VectorEntity)

    vector_field_name = "vector_"+distance_type.name.lower()
   
    values = [ 
        ("Power of red", [1, 1]),
        ("Blueberry", [2, 2]),
        ("Red", [3, 3]),
        ("Blue sea", [4, 4]),
        ("Lightblue", [5, 5]),
        ("Red apple", [6, 6]),
        ("Hundred", [7, 7]),
        ("Tired", [8, 8]),
        ("Power of blue", [9, 9])
    ]
    for value in values:
        entity = VectorEntity()
        setattr(entity, "name", value[0])
        setattr(entity, vector_field_name, value[1])
        box.put(entity)
        
    assert box.count() == 9

    # Test condition + NN search
    qb = box.query()
    qb.nearest_neighbors_f32(vector_field_name, [4.1, 4.2], 6)
    qb.contains_string("name", "red", case_sensitive=False)
    query = qb.build()
    # 4, 5, 3, 6, 2, 7
    # Filtered: 3, 6, 7
    search_results = query.find_with_scores()
    assert len(search_results) == 3
    assert search_results[0][0].name == "Red"
    assert search_results[1][0].name == "Red apple"
    assert search_results[2][0].name == "Hundred"

    # Test offset/limit on find_with_scores (result is ordered by score desc)
    query.offset(1)
    query.limit(1)
    search_results = query.find_with_scores()
    assert len(search_results) == 1
    assert search_results[0][0].name == "Red apple"

    # Regular condition + NN search
    qb = box.query()
    qb.nearest_neighbors_f32(vector_field_name, [9.2, 8.9], 7)
    qb.starts_with_string("name", "Blue", case_sensitive=True)
    query = qb.build()

    search_results = query.find_with_scores()
    assert len(search_results) == 1
    assert search_results[0][0].name == "Blue sea"

    # Regular condition + NN search
    qb = box.query()
    qb.nearest_neighbors_f32(vector_field_name, [7.7, 7.7], 8)
    qb.contains_string("name", "blue", case_sensitive=False)
    query = qb.build()
    # 8, 7, 9, 6, 5, 4, 3, 2
    # Filtered: 9, 5, 4, 2
    search_results = query.find_ids_with_scores()
    assert len(search_results) == 4
    assert search_results[0][0] == 9
    assert search_results[1][0] == 5
    assert search_results[2][0] == 4
    assert search_results[3][0] == 2

    search_results = query.find_ids_by_score()
    assert len(search_results) == 4
    assert search_results[0] == 9
    assert search_results[1] == 5
    assert search_results[2] == 4
    assert search_results[3] == 2

    search_results = query.find_ids_by_score_numpy()
    assert search_results.size == 4
    assert search_results[0] == 9
    assert search_results[1] == 5
    assert search_results[2] == 4
    assert search_results[3] == 2

    search_results = query.find_ids()
    assert len(search_results) == 4
    assert search_results[0] == 2
    assert search_results[1] == 4
    assert search_results[2] == 5
    assert search_results[3] == 9

    # Test offset/limit on find_ids (result is ordered by ID asc)
    query.offset(1)
    query.limit(2)
    search_results = query.find_ids()
    assert len(search_results) == 2
    assert search_results[0] == 4
    assert search_results[1] == 5

    # Test empty result
    query.offset(999)
    assert len(query.find_ids()) == 0
    assert len(query.find_ids_with_scores()) == 0
    assert len(query.find_ids_by_score()) == 0
    numpy_result = query.find_ids_by_score_numpy()
    assert numpy_result.size == 0
    assert str(numpy_result.dtype) == "uint64"
    assert len(numpy_result) == 0


def test_combined_nn_search():
    """ Tests NN search combined with regular query conditions, offset and limit. """
    distance_type = VectorDistanceType.EUCLIDEAN
    _test_combined_nn_search(distance_type)
    # TODO: Cosine, DotProduct  diverges see below
