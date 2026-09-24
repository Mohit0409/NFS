'use strict';

const assert = require('node:assert/strict');
const planner = require('./web/js/diet-planner.js');

function profile(overrides = {}) {
  return {
    age: 29,
    sex: 'male',
    weight: 78,
    height: 175,
    goal: 'loss',
    activity: 'moderate',
    gymDays: 4,
    diet: 'vegetarian',
    budget: 180,
    meals: 4,
    workout: 'evening',
    safety: true,
    ...overrides
  };
}

const indianGymUser = profile();
const targets = planner.calculateTargets(indianGymUser);
assert.equal(targets.calories, 2200);
assert.equal(targets.protein, 133);
assert.equal(targets.fibre, 25);

const vegetarianPlan = planner.buildPlan(indianGymUser, targets);
assert.equal(vegetarianPlan.blocked, false);
assert.equal(vegetarianPlan.meals.length, 4);
assert.ok(Math.abs(vegetarianPlan.totals.calories - targets.calories) < 2);
assert.ok(vegetarianPlan.totals.protein >= targets.protein * 0.95);
assert.ok(vegetarianPlan.totals.cost <= indianGymUser.budget);

const fiveMealProfile = profile({ sex: 'female', age: 35, weight: 60, height: 160, goal: 'maintain', activity: 'light', diet: 'vegan', budget: 220, meals: 5, workout: 'morning' });
const fiveMealPlan = planner.buildPlan(fiveMealProfile, planner.calculateTargets(fiveMealProfile));
assert.equal(fiveMealPlan.blocked, false);
assert.equal(fiveMealPlan.meals.length, 5);

const threeMealProfile = profile({ diet: 'eggetarian', budget: 250, meals: 3 });
const threeMealPlan = planner.buildPlan(threeMealProfile, planner.calculateTargets(threeMealProfile));
assert.equal(threeMealPlan.blocked, false);
assert.equal(threeMealPlan.meals.length, 3);

const nonVegProfile = profile({ diet: 'nonveg', budget: 120 });
const nonVegPlan = planner.buildPlan(nonVegProfile, planner.calculateTargets(nonVegProfile));
assert.equal(nonVegPlan.blocked, false);
assert.ok(nonVegPlan.totals.cost > nonVegProfile.budget);
assert.equal(planner.nearestPracticalBudget(nonVegPlan.totals.cost, nonVegProfile.budget) % 10, 0);
assert.ok(planner.nearestPracticalBudget(nonVegPlan.totals.cost, nonVegProfile.budget) >= Math.ceil(nonVegPlan.totals.cost));
assert.equal(planner.nearestPracticalBudget(213, 200), 220);
assert.equal(planner.nearestPracticalBudget(180, 200), 200);
assert.equal(planner.nearestPracticalBudget(180, 185), 185);
const validLowBudgetNonVeg = profile({ diet: 'nonveg', budget: 150 });
const validLowBudgetPlan = planner.buildPlan(validLowBudgetNonVeg, planner.calculateTargets(validLowBudgetNonVeg));
assert.ok(validLowBudgetPlan.totals.cost > validLowBudgetNonVeg.budget);
assert.equal(planner.nearestPracticalBudget(validLowBudgetPlan.totals.cost, validLowBudgetNonVeg.budget), 230);

assert.match(planner.validateProfile(profile({ safety: false })), /safety/i);
assert.match(planner.validateProfile(profile({ weight: 40, height: 170 })), /BMI/i);

const highBmiTargets = planner.calculateTargets(profile({ weight: 120, height: 170 }));
assert.ok(highBmiTargets.proteinWeight < 70);
assert.ok(highBmiTargets.protein < 130);

for (const sex of ['male', 'female']) {
  for (const goal of ['loss', 'gain', 'recomp', 'maintain']) {
    for (const diet of ['vegetarian', 'eggetarian', 'nonveg', 'vegan']) {
      for (const meals of [3, 4, 5]) {
        const matrixProfile = profile({
          sex,
          goal,
          diet,
          meals,
          weight: sex === 'male' ? 72 : 58,
          height: sex === 'male' ? 174 : 160,
          budget: 1000
        });
        assert.equal(planner.validateProfile(matrixProfile), '');
        const matrixTargets = planner.calculateTargets(matrixProfile);
        const matrixPlan = planner.buildPlan(matrixProfile, matrixTargets);
        assert.equal(matrixPlan.blocked, false, `${sex}/${goal}/${diet}/${meals}`);
        assert.equal(matrixPlan.meals.length, meals, `${sex}/${goal}/${diet}/${meals}`);
        assert.ok(Math.abs(matrixPlan.totals.calories - matrixTargets.calories) < 2);
        assert.ok(matrixPlan.totals.protein >= matrixTargets.protein * 0.88);
      }
    }
  }
}


const noGymProfile = profile({ goal: 'maintain', gymDays: 0, workout: 'none', meals: 5 });
assert.equal(planner.validateProfile(noGymProfile), '');
const noGymTargets = planner.calculateTargets(noGymProfile);
const trainedTargets = planner.calculateTargets(profile({ goal: 'maintain', gymDays: 6 }));
assert.ok(trainedTargets.calories > noGymTargets.calories, 'gym frequency must affect energy estimate');
const noGymPlan = planner.buildPlan(noGymProfile, noGymTargets);
assert.equal(noGymPlan.meals.some((meal) => /workout|recovery/i.test(meal.type)), false);

const morningProfile = profile({ goal: 'maintain', gymDays: 4, workout: 'morning', meals: 5 });
const morningPlan = planner.buildPlan(morningProfile, planner.calculateTargets(morningProfile));
assert.match(morningPlan.meals[0].type, /Pre-workout/);
assert.match(morningPlan.meals[1].type, /Post-workout breakfast/);

assert.match(planner.validateProfile(profile({ goal: 'gain', gymDays: 0, workout: 'none' })), /resistance training/i);
assert.match(planner.validateProfile(profile({ diet: 'nonveg', budget: 120 })), /₹150/);
assert.match(planner.validateProfile(profile({ age: 17 })), /18 and 65/);
assert.match(planner.validateProfile(profile({ weight: 20 })), /35 and 200/);
assert.match(planner.validateProfile(profile({ height: 120 })), /135 and 215/);

console.log('Diet planner tests: PASS');
