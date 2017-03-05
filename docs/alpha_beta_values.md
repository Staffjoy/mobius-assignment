# Alpha and Beta Values

Alpha and beta values are used to define the **worker shift weighting**, which is used to generate a happiness score.

The preference parameter is created to allow employees to designate shifts they prefer. The model then optimizes to give employees the shifts they desire. 

The happiness score matrix is defined by the **alpha value**, which is the upweight on a preferred shift, and the **beta value**, which is the downweight on a non-preferred shift. A worker who prioritizes all shifts or no shifts has both of these constants defined as zero. 

Generating the happiness score matrix requires two parameters: The availability matrix and the preferences matrix. Each of these is a binary matrix. A `1` in the availability matrix means that the worker is available (i.e. it is their working hours and they have not had an approved day off). A `1` in the preferences matrix means that the worker is available and prefers that shift. If availability is `0`, then the preference is overridden to `0`.

The happiness score matrix is calculated such that:

```python
# (warning: pseudocode)
sum(happpiness) == sum(availability)
```

The alpha and beta parameters are included such that:

```python
# For a given worker's availability and preferences
for day in week:
    for hour in hours:
        if availability[day][hour] == 0:
            happiness[day][hour] = 1
        elif preference[day][hour] == 1:
            happiness[day][hour] = 1 + alpha
        elif preference[day][hour] == 0:
            happiness[day][hour] = 1 - beta
```


Should an employee choose not to specify priority shifts, or if an employee chooses to prioritize all shifts, the preference matrix should thus be equally weighted, and exactly equal to the availability parameter.

Based on the objective function, priority shifts are upweighted, and based on the specified constraints the non-priority shifts must be downweighted. The upweighting factor is designated as **alpha** and the downweighting factor is designated as **beta**. 


Considering 4 shifts, of which one is prioritized:

``` (1 + alpha) + (1 - beta) + (1 - beta) + (1 - beta) = 4 ```

In this case, `alpha = 3 * beta`

Clearly, beta must always be less than one. However, we also consider that employees who specify only a single priority shift have more weight placed on that shift than someone who prioritizes all but one shift.  We specify that a prioritized shift may be no more than twice as weighted as a non-weighted shift, thus alpha is less than one.

Thus,

```
def calculate_alpha_beta(availability, preference):
    alpha = ( sum(availability) - sum(preference) ) / sum(availability)
    beta = (alpha * sum(preference) ) / (sum(availability) - sum(preference))

    return alpha, beta

```

## Unassigned Shifts

Shift weighting can also be considered while incorporating unassigned shifts. In general, unassigned shifts are only added when necessary - and are not considered favorable. For example, an unassigned shift should never cannibalize an assigned shift. It is better to have an unhappy worker in a shift than it is to have an unassigned shift. 

Thus, unassigned shifts should have a negative  happy matrix. By setting the offset to be a large negative value - e.g. an absolute `-100`, then we are essentially utilizing the [Big-M](https://en.wikipedia.org/wiki/Big_M_method) method on top of happiness weighting to prevent unassigned shifts from receiving priority in scheduling.

(Clarification - there is no weighting, alpha, or beta for unassigned shifts - they always incur a massive negative penalty whenever they are assigned.)

