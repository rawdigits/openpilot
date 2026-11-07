#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void live_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_9(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_12(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_35(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_32(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_update_33(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void live_H(double *in_vec, double *out_3453139176517170911);
void live_err_fun(double *nom_x, double *delta_x, double *out_3276522058452662963);
void live_inv_err_fun(double *nom_x, double *true_x, double *out_1014200675118784515);
void live_H_mod_fun(double *state, double *out_4551877506645921154);
void live_f_fun(double *state, double dt, double *out_1273833787517435005);
void live_F_fun(double *state, double dt, double *out_698610326700765083);
void live_h_4(double *state, double *unused, double *out_1318435814348717957);
void live_H_4(double *state, double *unused, double *out_6411919016161416104);
void live_h_9(double *state, double *unused, double *out_2348030026886849913);
void live_H_9(double *state, double *unused, double *out_4747606122283688042);
void live_h_10(double *state, double *unused, double *out_4437224670184986956);
void live_H_10(double *state, double *unused, double *out_430782562363623505);
void live_h_12(double *state, double *unused, double *out_773890188909891334);
void live_H_12(double *state, double *unused, double *out_7033018041209009771);
void live_h_35(double *state, double *unused, double *out_5886538081643074898);
void live_H_35(double *state, double *unused, double *out_8668163000175528136);
void live_h_32(double *state, double *unused, double *out_7126686007130249098);
void live_H_32(double *state, double *unused, double *out_2866858627967915578);
void live_h_13(double *state, double *unused, double *out_2320755905391482709);
void live_H_13(double *state, double *unused, double *out_2591084790657165657);
void live_h_14(double *state, double *unused, double *out_2348030026886849913);
void live_H_14(double *state, double *unused, double *out_4747606122283688042);
void live_h_33(double *state, double *unused, double *out_741360840326194815);
void live_H_33(double *state, double *unused, double *out_5517605995536670532);
void live_predict(double *in_x, double *in_P, double *in_Q, double dt);
}